"""
This script is an all-in-one demonstration including:

1) A "human-like" approach to Google searches:
   - Random user agents, random window sizes
   - Using a user-data-dir profile => persistent cookies
   - Step-by-step typed queries (simulate typing)
   - Random mouse moves, random intervals
   - BFS in Google results (we do up to 20 hits), 
     subpage BFS to locate "Kontakt," "Impressum," etc.
   - Up to 3 retries per step if stale element / timeouts occur
   - "Skip" if repeated failures => SkipEntryException

2) Cookie banner handling:
   - Multiple XPath selectors
   - "click_element_robust": tries direct .click() => fallback with ActionChains

3) Address / Keyword scoring:
   - If address tokens appear (Street, ZIP, City) => +3
   - If "kontakt"/"adresse"/<query> repeated => +2
   - Score >= 5 => relevant

4) E-Mail detection:
   - Normal e-mails
   - Obfuscated e-mails: (at), (dot), linkDecrypt('...')
   - Searching <meta> tags, <input type='hidden'>, entire page source

5) **Less generous phone detection**:
   - We removed overly broad phone patterns
   - We rely on stricter regex, so cryptic numbers won't pass
   - (Still can be improved if you face more specialized phone formats)

6) CSV output structure => [Name, Street, Zip, City, Website, Phone, Email]
   - The script processes each CSV row in parallel (ThreadPoolExecutor)
   - Writes partial results after each row

7) Big disclaimers:
   - Even with "human" behavior, Google might detect or throttle your scraping
   - If you have issues with cookie banners or missing phone #, adapt the code
   - If some phone # do not match your local format, refine the new phone regex
   - Ethical Usage: This repository aims at educational usage, not illicit data harvesting. 
   - Always ensure you have permission to scrape.
"""

import csv
import time
import random
import re
import logging
import threading
import os
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# Selenium & related exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementNotInteractableException,
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

################################################################################
# GLOBAL LOGGING CONFIG
################################################################################

logging.basicConfig(
    filename='scraper.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

################################################################################
# GLOBAL VARS
################################################################################

driver_counter = 0
restart_threshold = 30          # after every 30 CSV rows, we restart driver
MAX_RETRIES = 3                 # up to 3 attempts for certain failures
write_lock = threading.Lock()

GOOGLE_DOMAIN = "google.de"     # can adapt "google.com," etc.

################################################################################
# CUSTOM EXCEPTION => SKIP ENTRY
################################################################################

class SkipEntryException(Exception):
    """
    If we fail repeatedly (stale, timeouts, etc.), 
    we skip the current CSV row and store blank data.
    """
    pass

################################################################################
# USER AGENTS + WINDOW SIZES
################################################################################

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/110.0.5481.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (X11; Linux i686; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.0 Safari/605.1.15",
]
WINDOW_SIZES = [
    (1280,720),
    (1366,768),
    (1920,1080),
    (1536,864),
    (1440,900),
    (1600,900),
]

################################################################################
# BROWSER INIT
################################################################################

def init_driver():
    """
    1) choose random user agent
    2) choose random window size
    3) user-data-dir => persistent cookies
    """
    global driver

    ua = random.choice(USER_AGENTS)
    w,h= random.choice(WINDOW_SIZES)

    chrome_opts = Options()
    user_data_folder = os.path.join(os.getcwd(),"chrome_profile")
    if not os.path.exists(user_data_folder):
        os.makedirs(user_data_folder, exist_ok=True)

    chrome_opts.add_argument(f"--user-data-dir={user_data_folder}")
    chrome_opts.add_argument(f"--user-agent={ua}")
    chrome_opts.add_argument(f"--window-size={w},{h}")

    # No --ignore-certificate-errors => we skip if cert is invalid
    driver = webdriver.Chrome(service=Service(), options=chrome_opts)
    driver.set_page_load_timeout(20)
    driver.implicitly_wait(5)

################################################################################
# HUMAN-LIKE TYPING, RANDOM PAUSES, MOUSE MOVES
################################################################################

def human_type(element, text: str):
    """
    Type each character with a random delay 
    between 0.05 and 0.3 seconds.
    """
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.3))

def random_pause(base=1.0, var=2.0):
    """
    Sleep for base + random(0..var) seconds
    Example: random_pause(1,2) => 1..3 sec
    """
    t = base + random.random()*var
    time.sleep(t)

def random_mouse_move(driver):
    """
    Minimal offset-based move, 
    simulating a tiny mouse move
    """
    try:
        actions = ActionChains(driver)
        dx= random.randint(-40,40)
        dy= random.randint(-40,40)
        actions.move_by_offset(dx,dy).perform()
        random_pause(0.2,0.5)
        actions.move_by_offset(-dx,-dy).perform()
    except:
        pass

################################################################################
# do_infinite_scrolling => up to max_scroll times
################################################################################

def do_infinite_scrolling(driver, max_scroll=3, pause=1.0):
    """
    Scroll to bottom multiple times, waiting 'pause' each time
    and checking if we've reached the bottom.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

################################################################################
# ROBUST CLICK => SCROLL + ACTIONCHAINS
################################################################################

def click_element_robust(elem, tries=2):
    """
    1) direct elem.click()
    2) if that fails => scrollIntoView + ActionChains click
    up to 'tries' times
    """
    for i in range(tries):
        try:
            elem.click()
            return True
        except ElementNotInteractableException:
            logging.warning(f"element not interactable => attempt {i+1}, scrolling + actionchains fallback")
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                time.sleep(0.5)
                ActionChains(driver).move_to_element(elem).pause(0.5).click().perform()
                return True
            except Exception as e2:
                logging.warning(f"ActionChains fallback => {e2}")
        except Exception as ex:
            logging.warning(f"click_element_robust => {ex}")
            return False
    return False

################################################################################
# COOKIE BANNER => EXTENDED
################################################################################

def click_cookie_consent_if_present(driver):
    """
    We'll try several possible XPaths for cookie/consent. 
    If none is clickable => log that it's not critical.
    Using 'click_element_robust' to handle overlay issues.
    """
    possible_selectors = [
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'akzeptieren')]",
        "//button[contains(.,'Alle akzeptieren')]",
        "//button[contains(@id,'accept')]",
        "//button[contains(.,'Zustimmen')]",
        "//div[contains(.,'Zustimmen')]",
        "//button[@aria-label='Accept all']",
        "//button[contains(@class,'cookie') and contains(@class,'accept')]",
    ]
    for sel in possible_selectors:
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, sel))
            )
            success = click_element_robust(btn, tries=2)
            if success:
                time.sleep(1)
                logging.info(f"Cookie-Banner => clicked by selector: {sel}")
                return
        except:
            pass
    logging.info("Cookie-Banner => No matching selector found (not critical).")

################################################################################
# random_synonym_query => small variation
################################################################################

def random_synonym_query(name: str, street: str, plz: str, city: str) -> str:
    """
    Combine them into one query. 
    In 10% cases, "straße" => "strasse".
    """
    raw = f"{name} {street} {plz} {city}"
    if random.random() < 0.1:
        raw = raw.replace("straße","strasse")
    return raw

################################################################################
# safe_get => skip PDFs, skip cert invalid, up to 3 tries
################################################################################

def safe_get(url: str, attempt=1):
    """
    Use driver.get(url) but 
    - skip .pdf 
    - skip ERR_CERT_DATE_INVALID 
    - up to 3 attempts => else SkipEntryException
    """
    if url.lower().endswith(".pdf"):
        logging.info(f"SKIP PDF => {url}")
        return False
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME,"body"))
        )
        return True
    except WebDriverException as wex:
        msg = str(wex)
        if "ERR_CERT_DATE_INVALID" in msg:
            logging.info(f"Skipping insecure (cert) => {url}")
            return False
        logging.warning(f"WebDriverException => {msg}, attempt={attempt}")
        if attempt >= MAX_RETRIES:
            raise SkipEntryException(f"Too many failures => {url}")
        random_pause(1,1.5)
        return safe_get(url, attempt+1)
    except TimeoutException:
        logging.warning(f"Timeout => attempt={attempt}, url={url}")
        if attempt >= MAX_RETRIES:
            raise SkipEntryException(f"Timeout x3 => {url}")
        random_pause(1,1.5)
        return safe_get(url, attempt+1)

################################################################################
# EVALUATION => ADDRESS / KEYWORDS => SCORE
################################################################################

def normalize_address_part(s: str) -> str:
    """ 
    lowercase, unify special chars, unify 'straße' 
    """
    s = s.lower()
    s = s.replace("ü","u").replace("ö","o").replace("ä","a").replace("ß","ss")
    s = s.replace("str.","straße").replace("strasse","straße").replace("strass","straße")
    return s

def tokenize_address_component(s: str) -> list:
    s = normalize_address_part(s)
    return [p.strip() for p in s.replace("-"," ").split() if p.strip()]

def address_score(page_source: str, street: str, plz: str, city: str) -> int:
    """
    +2 if PLZ + City tokens found
    +1 if street tokens found
    => total up to 3
    """
    pn = normalize_address_part(page_source)
    st = tokenize_address_component(street)
    pz = tokenize_address_component(plz)
    ct = tokenize_address_component(city)

    sc=0
    if all(t in pn for t in pz) and all(t in pn for t in ct):
        sc += 2
    if all(t in pn for t in st):
        sc += 1
    return sc

def is_address_present_relaxed(page_source: str, street: str, plz: str, city: str) -> bool:
    return address_score(page_source, street, plz, city) >= 2

def keyword_density(page_source: str, keywords: list) -> bool:
    """
    We consider a  >5 match threshold
    """
    pn = normalize_address_part(page_source)
    hits = 0
    for kw in keywords:
        hits += pn.count(kw.lower())
    return hits > 5

def evaluate_page(page_source: str, name: str, street: str, plz: str, city: str) -> bool:
    """
    +3 => address present
    +2 => keyword density => total >=5 => relevant
    """
    sc=0
    kw = [name.lower(),"kontakt","adresse"]
    if is_address_present_relaxed(page_source, street, plz, city):
        sc += 3
    if keyword_density(page_source, kw):
        sc += 2
    return (sc >= 5)

################################################################################
# PHONE / EMAIL => LESS GENEROUS PHONE DETECTION
################################################################################

def antiSpamMailDecode(encoded_string: str) -> str:
    """
    SHIFT -1 for antiSpamMail.linkDecrypt('...')
    """
    res=[]
    for c in encoded_string:
        shifted = chr(ord(c)-1)
        res.append(shifted)
    return "".join(res)

def parse_meta_tags(driver) -> str:
    metas = driver.find_elements(By.TAG_NAME,"meta")
    lines= []
    for m in metas:
        c = m.get_attribute("content") or ""
        if c.strip():
            lines.append(c.strip())
    return "\n".join(lines)

def parse_hidden_inputs(driver) -> str:
    hiddens = driver.find_elements(By.CSS_SELECTOR,"input[type='hidden']")
    val= []
    for h in hiddens:
        v = h.get_attribute("value") or ""
        if v.strip():
            val.append(v.strip())
    return "\n".join(val)

def parse_less_generous_phones(text: str):
    """
    We define a 'less generous' phone regex 
    to avoid cryptic matches.

    Requirements:
    - Usually a phone number might have:
      +49 or +something for country code
      optional parentheses for area code (0xxx)
      at least 6-7 total digits to be plausible
    - We also detect patterns like 'Telefon: +49...' 
      or 'Tel: 0176...'
    """
    # Option 1: explicitly matching if "tel|phone" is in prefix
    phone_prefix_pattern = re.compile(
        r'(?:tel|phone|call)[:\s]*(\+?\d{2,4}\(?\d{1,4}\)?\s?\d{3,}[\d\s/\-]*)',
        re.IGNORECASE
    )
    # Option 2: a simpler general pattern for e.g. '+49 (0) 1234 5678'
    # ignoring too short or cryptic combos
    phone_simple_pattern = re.compile(
        r'\+?\d{2,4}[\s./-]*\(?\d{1,4}\)?[\s./-]*\d{3,}[\d\s./-]*',
        re.IGNORECASE
    )

    phones_found = set()

    # prefix-based
    for match in phone_prefix_pattern.finditer(text):
        # ensure it's decently sized
        phone_candidate = match.group(1).strip()
        # check minimal length
        if len(re.sub(r'\D','',phone_candidate)) >= 7:
            phones_found.add(phone_candidate)

    # simpler pattern
    for mat in phone_simple_pattern.finditer(text):
        phone_candidate = mat.group(0).strip()
        # again, check length in digits
        if len(re.sub(r'\D','',phone_candidate)) >= 7:
            phones_found.add(phone_candidate)

    return phones_found

def parse_phone_and_email_obfuscated(big_source: str):
    """
    Parse e-mails & phone from entire text fallback.

    *Emails*:
      - normal
      - obf => 'user (at) domain (dot) tld'
    *Phones*:
      - we rely on parse_less_generous_phones
    """
    # Normal email pattern
    normal_mail = re.compile(
        r'[a-zA-Z0-9._%+\-\(\)]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
        re.MULTILINE
    )
    # Obfuscated email => user (at) domain (dot) tld
    obf_mail = re.compile(
        r'([a-zA-Z0-9._%+\-]+)\s?(\(|\[)?at(\)|\])?\s?([a-zA-Z0-9.\-]+)\s?'
        r'(\(|\[)?(dot|punkt)(\)|\])?\s?([a-zA-Z]{2,})',
        re.IGNORECASE
    )

    phones_found = set()
    mails_found = set()

    # parse phone (less generous)
    phone_candidates = parse_less_generous_phones(big_source)
    for pc in phone_candidates:
        phones_found.add(pc.strip())

    # normal mail
    for match in normal_mail.findall(big_source):
        mails_found.add(match.strip())

    # obf mail
    for match in obf_mail.finditer(big_source):
        user = match.group(1)
        dom = match.group(4)
        tld = match.group(8)
        final = f"{user}@{dom}.{tld}"
        mails_found.add(final.strip())

    return phones_found, mails_found

def parse_phone_email_deep(driver):
    """
    1) Combine page source + <meta> + hidden <input>
    2) In <a> => 'tel:', 'mailto:', linkDecrypt...
    3) Fallback => parse_less_generous_phones in entire text
    """
    page_src = driver.page_source
    meta_txt = parse_meta_tags(driver)
    hidden_txt = parse_hidden_inputs(driver)
    combined = "\n".join([page_src, meta_txt, hidden_txt])

    phone_set = set()
    mail_set  = set()

    # search <a> tags
    links = driver.find_elements(By.TAG_NAME,"a")
    for link in links:
        try:
            href= link.get_attribute("href") or ""
            txt= link.text or ""

            # if "tel:" => direct phone
            if href.lower().startswith("tel:"):
                phone_candidate = href[4:].strip()
                # quick check => 7 digits min
                if len(re.sub(r'\D','',phone_candidate))>=7:
                    phone_set.add(phone_candidate)

            # if "mailto:"
            elif href.lower().startswith("mailto:"):
                mail_set.add(href[7:].strip())

            # linkDecrypt => SHIFT -1
            elif "linkdecrypt" in href.lower():
                encs= re.findall(r"linkDecrypt\('([^']+)'\)", href, re.IGNORECASE)
                for e in encs:
                    dec= antiSpamMailDecode(e)
                    if dec.startswith("mailto:"):
                        mail_set.add(dec[7:].strip())

            # text => if it says "Tel." or "Telefon:" => parse that portion
            if "telefon:" in txt.lower() or "tel." in txt.lower():
                # we just parse the entire text 
                # with parse_less_generous_phones:
                p_candidates = parse_less_generous_phones(txt)
                for pc in p_candidates:
                    phone_set.add(pc.strip())

        except StaleElementReferenceException:
            logging.warning("Stale link => skipping phone/email parse.")
            continue

    # fallback => entire combined => parse phone/e-mail obf
    phs, ems= parse_phone_and_email_obfuscated(combined)
    for p in phs:
        phone_set.add(p.strip())
    for e in ems:
        mail_set.add(e.strip())

    phone= next(iter(phone_set), None)
    email= next(iter(mail_set), None)
    return phone, email

################################################################################
# SUBPAGE BFS
################################################################################

IMPO_KEYWORDS= ["impressum","kontakt","datenschutz","imprint","privacy"]

def link_priority(e):
    """
    If text/href has 'impressum/kontakt' => 0 => higher prio
    else => 1
    """
    try:
        txt= (e.text or "").lower()
        href= (e.get_attribute("href") or "").lower()
        for kw in IMPO_KEYWORDS:
            if kw in txt or kw in href:
                return 0
    except:
        pass
    return 1

def search_subpages(base_url: str, street: str, plz: str, city: str, 
                    max_depth=2, attempt=1):
    """
    BFS recursion up to 'max_depth'
    We do:
     1) safe_get => skip PDF/cert
     2) do_infinite_scrolling
     3) evaluate_page => if relevant => return
     4) gather up to 30 <a> => sorted by link_priority => 
        process each => recursion depth-1
    """
    if base_url.lower().endswith(".pdf"):
        logging.info(f"Skip PDF subpage => {base_url}")
        return base_url
    ok = safe_get(base_url, attempt=attempt)
    if not ok:
        return base_url

    # scroll
    do_infinite_scrolling(driver, max_scroll=3, pause=1.2)
    ps= driver.page_source
    if evaluate_page(ps, base_url, street, plz, city):
        return base_url

    if max_depth<=0:
        return base_url

    visited = set()
    alinks = driver.find_elements(By.TAG_NAME,"a")[:30]
    s_alinks = sorted(alinks, key=link_priority)

    for idx, link in enumerate(s_alinks):
        try:
            href= link.get_attribute("href")
        except StaleElementReferenceException:
            logging.warning(f"Stale subpage BFS => attempt={attempt}")
            if attempt>=MAX_RETRIES:
                raise SkipEntryException("subpages => stale => skip")
            time.sleep(1)
            fresh= driver.find_elements(By.TAG_NAME,"a")[:30]
            if idx<len(fresh):
                link= fresh[idx]
                try:
                    href= link.get_attribute("href")
                except:
                    href= None
            else:
                href=None

        if not href:
            continue
        if href.lower().endswith(".pdf"):
            logging.info(f"Skip PDF => {href}")
            continue

        dom= urlparse(href).netloc.lower()
        if dom== urlparse(base_url).netloc.lower() and href not in visited:
            visited.add(href)
            sub_url= search_subpages(href, street, plz, city, max_depth-1, attempt=attempt)
            if sub_url!= href:
                return sub_url

    return base_url

################################################################################
# GOOGLE SEARCH BFS
################################################################################

def is_relevant_url(query, url):
    """
    We skip blob:, data:, .pdf, blacklisted keywords, TLD checks
    Then we see if any query part is in the domain => relevant
    """
    if url.lower().startswith("blob:") or url.lower().startswith("data:"):
        return False
    if url.lower().endswith(".pdf"):
        return False

    domain= urlparse(url).netloc.lower()

    allowed_tlds = [
        '.de','.com','.net','.org','.info','.eu','.co','.at','.ch','.shop',
        '.auto','.website','.online'
    ]
    blacklist_keywords = [
        'facebook','instagram','linkedin','stepstone','indeed','twitter','xing',
        'karriere','meinestadt','ebay','booking','youtube','pinterest',
        'autoscout','mobile.de','gelbeseiten','dastelefonbuch','.pdf'
    ]
    if not any(tld in domain for tld in allowed_tlds):
        return False
    if any(kw in domain for kw in blacklist_keywords):
        return False

    query_norm= query.lower()
    domain_norm= domain
    query_parts= query_norm.split()
    return any(part in domain_norm for part in query_parts)

def google_search(name:str, street:str, plz:str, city:str, attempt=1):
    """
    BFS: up to 20 google results,
    shuffle them,
    if 'is_relevant_url' => we load => check 'evaluate_page' => subpages => parse phone/email
    """
    global driver_counter, driver

    if driver_counter%restart_threshold==0 and driver_counter!=0:
        logging.info("Restart driver => threshold")
        try:
            driver.quit()
        except:
            pass
        init_driver()

    driver_counter +=1

    query= random_synonym_query(name, street, plz, city)
    google_url= f"https://www.{GOOGLE_DOMAIN}/"
    ok= safe_get(google_url, attempt=attempt)
    if not ok:
        return None,None,None

    random_pause(1,1.5)
    try:
        click_cookie_consent_if_present(driver)
    except:
        pass

    try:
        sb= WebDriverWait(driver,10).until(
            EC.element_to_be_clickable((By.NAME,"q"))
        )
    except:
        if attempt>=MAX_RETRIES:
            raise SkipEntryException("No search box => skip")
        return None,None,None

    # type
    human_type(sb, query)
    random_pause(0.5,1.0)
    sb.send_keys(Keys.RETURN)
    random_pause(1,2)

    try:
        WebDriverWait(driver,8).until(
            EC.presence_of_element_located((By.ID,"search"))
        )
    except:
        if attempt>=MAX_RETRIES:
            raise SkipEntryException("No google results => skip")
        return None,None,None

    do_infinite_scrolling(driver, max_scroll=2, pause=1.0)
    glinks= driver.find_elements(By.XPATH,"//a[contains(@href,'http')]")
    top= glinks[:20]
    random.shuffle(top)

    for idx, link in enumerate(top):
        href=None
        try:
            href= link.get_attribute("href")
        except StaleElementReferenceException as se:
            if attempt>=MAX_RETRIES:
                raise SkipEntryException(f"stale google link => skip => {se}")
            time.sleep(1)
            fresh= driver.find_elements(By.XPATH,"//a[contains(@href,'http')]")[:20]
            if idx<len(fresh):
                link= fresh[idx]
                href= link.get_attribute("href")

        if not href:
            continue
        if href.lower().endswith(".pdf"):
            logging.info(f"skip pdf => {href}")
            continue

        q= f"{name} {street} {plz} {city}"
        if not is_relevant_url(q, href):
            continue

        loaded= safe_get(href, attempt=attempt)
        if not loaded:
            continue

        do_infinite_scrolling(driver, max_scroll=3, pause=1.2)
        ps= driver.page_source
        if evaluate_page(ps, name, street, plz, city):
            # subpages => BFS
            sub_url= search_subpages(href, street, plz, city, max_depth=2, attempt=attempt)
            loaded2= safe_get(sub_url, attempt=attempt)
            if loaded2:
                do_infinite_scrolling(driver, max_scroll=1, pause=1.0)
                phone, email= parse_phone_email_deep(driver)
                return sub_url, phone, email

        # optionally => driver.back
        if random.random()<0.7:
            driver.back()
            random_pause(0.7,1.5)

    return None,None,None

################################################################################
# CSV => [Name, Street, Zip, City, Website, Phone, Email]
################################################################################

def save_results(results, output_file):
    with write_lock:
        with open(output_file,"w",newline="",encoding="utf-8") as cf:
            writer= csv.writer(cf)
            writer.writerow(["Name","Street","Zip","City","Website","Phone","Email"])
            writer.writerows(results)

################################################################################
# PROCESS_ROW
################################################################################

def process_row(row, results, output_file):
    """
    For each CSV row => google_search => subpages => parse => CSV
    If repeated fails => skip => empty row
    """
    try:
        if len(row)!=4:
            raise ValueError(f"Invalid row => {row}")
        name, street, plz, city= row
        logging.info(f"Processing => {name} {street} {plz} {city}")

        found_url, phone, email= google_search(name, street, plz, city)
        results.append([
            name, street, plz, city,
            found_url if found_url else "",
            phone if phone else "",
            email if email else ""
        ])
        save_results(results, output_file)
        random_pause(1,2)

    except SkipEntryException as sk:
        logging.warning(f"SKIP => {sk}")
        results.append([row[0], row[1], row[2], row[3], "", "", ""])
        save_results(results, output_file)

    except Exception as e:
        logging.warning(f"process_row => {e}")
        results.append([row[0], row[1], row[2], row[3], "", "", ""])
        save_results(results, output_file)

################################################################################
# MAIN
################################################################################

def main():
    """
    1) init_driver
    2) read CSV 'adressen.csv'
    3) for each row => process in a single ThreadPool
    4) finalize => close driver
    """
    results=[]
    input_file= "adressen.csv"
    output_file= "ergebnisse.csv"

    init_driver()

    with open(input_file,"r",encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=",")
        with ThreadPoolExecutor(max_workers=1) as executor:
            tasks=[]
            for row in reader:
                tasks.append(executor.submit(process_row, row, results, output_file))
            for t in tasks:
                t.result()

    driver.quit()
    logging.info("All rows done => " + output_file)

################################################################################
# LAUNCH
################################################################################

if __name__=="__main__":
    main()
