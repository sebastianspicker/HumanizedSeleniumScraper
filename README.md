# HumanizedSeleniumScraper
A Python script that automates "human-like" Google searches with Selenium, including subpage BFS,  robust cookie banner handling, address/keyword checks, and phone/email detection.

# Humanized-Selenium-Google-Scraper

A Python-based project aiming to scrape Google search results **as humanly as possible** using Selenium. This script types queries character by character, randomly moves the mouse, handles cookie banners, explores subpages up to a defined depth, and attempts to detect phone numbers/emails (including obfuscated ones). It also includes address/keyword checks to deem pages "relevant."

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
   # or venv\Scripts\activate on Windows
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
