# HumanizedSeleniumScraper
A Python-based project aiming to scrape Google search results **as humanly as possible** using Selenium including subpage BFS,  robust cookie banner handling, address/keyword checks, and phone/email detection. This script types queries character by character, randomly moves the mouse, handles cookie banners, explores subpages up to a defined depth, and attempts to detect phone numbers/emails (including obfuscated ones). It also includes address/keyword checks to deem pages "relevant."

---

## Features

- **"Human-Like" Google Searching**  
  - Random user agents & window sizes (simulating different machines).  
  - Typing each character with short random pauses.  
  - Basic mouse moves to reduce bot-likeness.  
  - Random waiting intervals.

- **Cookie Banner Handling**  
  - Multiple potential XPaths for "Accept"/"Zustimmen" etc.  
  - Scrolls the button into view + `ActionChains` fallback if direct click fails.

- **Subpage BFS**  
  - Gathers links from the loaded page, prioritizes "Impressum" or "Kontakt."  
  - Explores them up to `max_depth=2`.

- **Address/Keyword Relevance**  
  - Token-based checking for street, ZIP, city.  
  - Counts repeated terms like `kontakt`, `adresse`, plus the initial query.  
  - A final "score" decides if the page is relevant.

- **Less Generous Phone Detection**  
  - Avoids “cryptic” numeric strings by using stricter patterns.  
  - Checks for minimal digit counts (≥7).  
  - Considers typical phone prefixes (`tel|phone|call`).

- **Email Detection**  
  - Recognizes normal emails + obfuscated ones: `(at)`, `(dot)`, or `linkDecrypt('...')`.  
  - Searches `<meta>` tags, `<input type="hidden">`, entire page source.

- **3-Retries Error Handling**  
  - Retrys timeouts, stale elements, or certificate errors.  
  - If repeated failures => skip row.

- **Parallelization**  
  - Uses Python's `ThreadPoolExecutor` to process CSV rows in separate tasks.

- **CSV Output**  
  - Writes `[Name, Street, Zip, City, Website, Phone, Email]` per row.

---

## Installation

1. **Clone** this repository:
   ```bash
   git clone https://github.com/YourUsername/Humanized-Selenium-Google-Scraper.git
   cd Humanized-Selenium-Google-Scraper
2. Set up a virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   or venv\Scripts\activate on Windows
3. Install dependencies:
   pip install -r requirements.txt
   Make sure you have a matching version of chromedriver for your local Chrome/Chromium.
4. Prepare your CSV:
   By default, it expects adresses.csv with four columns: [Name, Street, Zip, City].
   Comma-separated, no header row.
5. Run:
   python HumanizedSeleniumScraper.py
   The script will generate an results.csv (or whichever output file you define).

## Usage

- Change Google TLD
  - If you prefer google.com, set: GOOGLE_DOMAIN = "google.com"
- Adapt Cookie Banner XPaths
  - In click_cookie_consent_if_present(), adjust or add XPaths if your site’s cookie overlay differs.
- Adapt Phone Regex
  - In parse_less_generous_phones(), refine or replace patterns to match local phone formatting.
- Address Normalization
  - Functions like normalize_address_part() unify strings like "Str." => "straße".
- Thread Count
  - By default, the script uses ThreadPoolExecutor(max_workers=1). Increase if you want multiple rows processed in parallel.
- Log File
  - All major actions and warnings are logged in scraper.log.
 
## How It Works

- init_driver()
  - Chooses a random user agent & window size, sets up a user-data directory so cookies persist across runs.

- process_row(row, ...)
  - Builds a search query from [Name, Street, Zip, City].
  - Launches google_search(...).
  - If relevant results are found, subpages are also checked (BFS).
  - Once we have a final “relevant” site, we parse phone & email.
  - Writes the final row to ergebnisse.csv.

- “Human-Like” Tactics
  - We type each letter with short random delays (0.05–0.3s).
  - Insert random waits (random_pause(...)) at each step.
  - Occasionally do small mouse movements to mimic user action.
  - BFS in Google => up to 20 links per page.

- Phone/Email Extraction
  - <a href='tel:'> or 'mailto:'>
  - Searching for strings like 'Telefon: +49...' or 'phone: ...'.
  - Fallback regex in entire combined text.

Below is a **`requirements.txt`** file, a short description for a **Beta01** release, and an **explanation** of how to adjust the script to individual needs.

---

## **Adapting the Script to Individual Needs**

### 1. **Cookie Banner Overlay**

- Look at the `click_cookie_consent_if_present(driver)` function.  
- If your target sites have different acceptance buttons, edit the **XPath** patterns or add new ones in `possible_selectors`.  
- If an overlay is inside an iframe, you may need to switch frames with `driver.switch_to.frame(...)`.  

### 2. **Google Domain**

- By default, the script uses `google.de`.  
- Switch to `google.com` or a country-specific domain:
  ```python
  GOOGLE_DOMAIN = "google.com"
  ```

### 3. **User Agents & Window Sizes**

- The lists `USER_AGENTS` and `WINDOW_SIZES` define random “profiles.”  
- If you want a consistent environment, **fix** the size (e.g., always `1920,1080`) or replace the random user agents with a static one:
  ```python
  USER_AGENTS = [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " 
      "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
  ]
  WINDOW_SIZES = [
      (1920, 1080)
  ]
  ```

### 4. **Phone Detection**  
- The function `parse_less_generous_phones(text)` tries to avoid matching incomplete or cryptic strings.  
- If you have region-specific patterns (e.g., different country codes, length requirements), update or add regexes:
  ```python
  # Example for a stricter format 
  phone_prefix_pattern = re.compile(r'(?:tel|phone)[:\s]*(\+49\s?\d+\s?\d+)', re.IGNORECASE)
  ```

### 5. **Address Normalization**  
- In `normalize_address_part()`, you can unify more local synonyms (e.g., `'rd.' => 'road'`, `'ave.' => 'avenue'`) if you deal with different locales.  
- Expand or remove existing replacements for `str.` => `straße` if you do not need German forms.

### 6. **Relevance Scoring**  
- The `evaluate_page(...)` function uses a threshold **score >= 5**.  
- If your data only rarely matches street tokens, you might lower or raise the threshold or add custom keywords. For example:
  ```python
  if is_address_present_relaxed(page_source, street, zip_code, city):
      score += 2   # Lower from 3 to 2
  if keyword_density_check(page_source, [query.lower(), "kontakt", "adresse"]):
      score += 3   # Increase from 2 to 3
  # => new total >= 5 ...
  ```

### 7. **Thread Count**

- By default, the script uses:
  ```python
  with ThreadPoolExecutor(max_workers=1) as executor:
      ...
  ```
- Increase `max_workers` if you want more parallel rows processed. Keep in mind, Google might detect rapid requests, so proceed carefully:
  ```python
  max_workers = 3  # or higher, if your environment can handle it
  ```

### 8. **Error Handling / Retries**

- The script automatically retries up to **3 times** for timeouts or stale elements.  
- If your environment is slow or you face frequent timeouts, you can:
  ```python
  MAX_RETRIES = 5
  driver.set_page_load_timeout(30)
  driver.implicitly_wait(10)
  ```
- Or handle additional exceptions if needed.

### 9. **Output / Logging**

- The script writes partial results after each CSV row to `ergebnisse.csv`.  
- A full debug timeline is in `scraper.log`.  
- If you need a different output location or format (e.g., TSV, JSON), adapt `save_results(...)`.

### 10. **“Human-like” Tuning**

- Adjust the **range of random pauses** in `random_pause(base, var)` or character-typing speed in `human_type(...)`.  
- Increase or decrease **mouse-move frequency** for more or fewer “human” illusions.

---
 
## Disclaimer

1. Respect Terms of Service
   Automated scraping of Google may violate Google’s TOS.
   Use responsibly and check local regulations.

2. No Guarantee
   This script is a demonstration. Google can still detect patterns or block IP addresses.
   We do not assume liability for blocked requests or policy infringements.

3. Ethical Usage
   This repository aims at educational usage, not illicit data harvesting.
   Always ensure you have permission to scrape.

## License

MIT License:
You’re free to use, modify, and distribute. See LICENSE for details.
