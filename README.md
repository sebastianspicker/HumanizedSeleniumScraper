# HumanizedSeleniumScraper
A Python-based project aiming to scrape Google search results **as humanly as possible** using Selenium including subpage BFS,  robust cookie banner handling, address/keyword checks, and phone/email detection. This script types queries character by character, randomly moves the mouse, handles cookie banners, explores subpages up to a defined depth, and attempts to detect phone numbers/emails (including obfuscated ones). It also includes address/keyword checks to deem pages "relevant."

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

## Known Issues and Fixes

1. **Network Service Crashed, Restarting**  
   - **Example Log Snippet:**
     ```
     [10408:8496:0105/141735.696:ERROR:network_service_instance_impl.cc(613)] 
     Network service crashed, restarting service.
     ```
   - **Explanation:**  
     Sometimes Chrome’s network service may crash internally, causing this message to appear. This does not necessarily disrupt the entire script, but it can lead to intermittent connectivity issues or unexpected browser behavior.
   - **Potential Solutions:**  
     - Update both **Chrome** and **Chromedriver** to the latest versions to reduce internal crashes.  
     - Ensure that no external antivirus/firewall programs are interfering with Chrome’s internal network processes.  
     - If the crash recurs frequently, consider adding a small **random pause** or a **driver restart** strategy after N rows to stabilize the session.

2. **Device/USB Property Not Found**  
   - **Example Log Snippet:**
     ```
     [10408:8496:0105/141737.771:ERROR:device_event_log_impl.cc(201)] 
     [14:17:37.771] USB: usb_service_win.cc:105 
     SetupDiGetDeviceProperty({{A45C254E-DF1C-4EFD-8020-67D146A850E0}, 6}) 
     failed: Element not found. (0x490)
     ```
   - **Explanation:**  
     This is a **Windows-specific** error indicating it could not retrieve certain USB-related device properties. It typically does **not** affect Selenium scraping itself, but rather the underlying browser’s attempt to manage or query USB devices.
   - **Potential Solutions:**  
     - You can safely **ignore** this error if the script continues without issues.  
     - If it repeats excessively, updating **Windows drivers** or disabling Chrome’s USB detection features (`--disable-usb-devices`) might help.  
     - Confirm that no USB-related policies are blocking Chrome from enumerating devices.

3. **SSL Handshake Failed**  
   - **Example Log Snippet:**
     ```
     [18156:23440:0105/141932.144:ERROR:ssl_client_socket_impl.cc(878)] 
     handshake failed; returned -1, SSL error code 1, net_error -201
     ```
   - **Explanation:**  
     Chrome encountered a TLS/SSL issue with the remote site (e.g., an invalid certificate, handshake mismatch).  
   - **Potential Solutions:**  
     - If the site truly has an invalid or expired certificate, the script will skip it when encountering `ERR_CERT_DATE_INVALID`.  
     - Check that your system’s **date/time** is correct.  
     - If you trust the site, you might forcibly allow insecure connections (though that can undermine the “skip invalid cert” approach).

4. **Sandbox Cannot Access Executable**  
   - **Example Log Snippet:**
     ```
     [10408:5044:0105/142035.622:ERROR:sandbox_win.cc(791)] 
     Sandbox cannot access executable. 
     Check filesystem permissions are valid. 
     See https://bit.ly/31yqMJR.: Access denied (0x5)
     ```
   - **Explanation:**  
     This is a **Windows** permissions issue indicating that the Chrome/Chromedriver sandbox lacks the necessary rights to run or access certain files.  
   - **Potential Solutions:**  
     - **Run as Administrator** or ensure the user running the script has full read/execute permissions for `chromedriver.exe` and the script folder.  
     - Ensure your antivirus or security software is not blocking the sandbox from accessing executables.  
     - Try placing `chromedriver.exe` in a simple path like `C:\Selenium\chromedriver.exe` with correct permissions, then reference that path in your code.

5. **Element Not Interactable**  
   - **Explanation:**  
     Selenium attempts to click or type into an element that is hidden, covered by an overlay (like a cookie banner), or not yet in view.  
   - **Potential Solutions:**  
     - Use **`click_element_robust`** with scrolling + ActionChains fallback.  
     - Wait explicitly for an element to become visible (e.g., `EC.visibility_of_element_located` instead of `EC.element_to_be_clickable`).  
     - Ensure you have correct **selectors** for responsive layouts or different window sizes.

6. **Cookie Banner Not Found** / “No Matching Selector”  
   - **Explanation:**  
     The script tries multiple selectors for “accept” or “Zustimmen,” but your site might label them differently or place them inside iframes.  
   - **Potential Solutions:**  
     - Add or adapt your own XPaths in `click_cookie_consent_if_present(...)`.  
     - If the overlay is nested in an iframe, switch frames with `driver.switch_to.frame(...)` before searching for the button.

7. **Excessive CPU or Memory Usage**  
   - **Explanation:**  
     Because of infinite scrolling or repeated BFS, the browser can use substantial system resources.  
   - **Potential Solutions:**  
     - Limit `max_scroll`, reduce BFS depth, or close the driver more often.  
     - Lower `max_workers` in `ThreadPoolExecutor` if you are running multiple parallel tasks.

8. **Phone Detection Gaps**  
   - **Explanation:**  
     Even with “less generous” patterns, certain phone formats or local numbering schemes might still be missed. Alternatively, some partial matches might slip through.  
   - **Potential Solutions:**  
     - Adapt `parse_less_generous_phones` with additional country-specific formatting checks.  
     - Filter by prefix (like `+49` or `+1`) or minimum length to match local guidelines.

9. **Google Captcha / Throttling**  
   - **Explanation:**  
     If you do repeated high-volume queries, Google might present a **CAPTCHA** or temporarily block your IP.  
   - **Potential Solutions:**  
     - Add **longer random pauses** between queries.  
     - Use fewer concurrency workers.  
     - Potentially rotate IP addresses (though this is beyond the scope of this script, and can have policy implications).

**Additional Note**: The script’s success heavily depends on **keeping your Chrome/Chromedriver versions in sync** and ensuring you have local filesystem permissions. If you encounter persistent errors with driver initialization or timeouts, double-check that your environment (OS, Python version, Selenium version) is properly configured.


## Disclaimer

### 1. Respect Terms of Service:
   Automated scraping of Google may violate Google’s TOS.
   Use responsibly and check local regulations.

### 2. No Guarantee:
   This script is a demonstration. Google can still detect patterns or block IP addresses.
   We do not assume liability for blocked requests or policy infringements.

### 3. Ethical Usage:
   This repository aims at educational usage, not illicit data harvesting.
   Always ensure you have permission to scrape.

## License

MIT License:
You’re free to use, modify, and distribute. See LICENSE for details.
