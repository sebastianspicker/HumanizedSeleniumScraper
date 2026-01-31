from __future__ import annotations

import logging
import time

from selenium.common.exceptions import (
    ElementNotInteractableException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import ScraperConfig
from .exceptions import SkipEntryError
from .human import random_pause


def click_element_robust(driver, elem, tries: int = 2) -> bool:
    for attempt in range(tries):
        try:
            elem.click()
            return True
        except ElementNotInteractableException:
            logging.warning(
                "element not interactable (attempt %s) => scroll + actionchains fallback",
                attempt + 1,
            )
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                time.sleep(0.5)
                ActionChains(driver).move_to_element(elem).pause(0.5).click().perform()
                return True
            except Exception as exc:
                logging.warning("ActionChains fallback failed: %s", exc)
        except Exception as exc:
            logging.warning("click_element_robust failed: %s", exc)
            return False
    return False


def click_cookie_consent_if_present(driver) -> None:
    possible_selectors = [
        (
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'akzeptieren')]"
        ),
        "//button[contains(.,'Alle akzeptieren')]",
        "//button[contains(@id,'accept')]",
        "//button[contains(.,'Zustimmen')]",
        "//div[contains(.,'Zustimmen')]",
        "//button[@aria-label='Accept all']",
        "//button[contains(@class,'cookie') and contains(@class,'accept')]",
    ]
    for selector in possible_selectors:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, selector)))
            if click_element_robust(driver, btn, tries=2):
                time.sleep(1)
                logging.info("Cookie-Banner clicked by selector: %s", selector)
                return
        except Exception:
            continue
    logging.info("Cookie-Banner: no matching selector found (not critical).")


def safe_get(driver, config: ScraperConfig, url: str, *, attempt: int = 1) -> bool:
    if url.lower().endswith(".pdf"):
        logging.info("SKIP PDF => %s", url)
        return False
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return True
    except WebDriverException as exc:
        msg = str(exc)
        if "ERR_CERT_DATE_INVALID" in msg:
            logging.info("Skipping insecure (cert) => %s", url)
            return False
        logging.warning("WebDriverException => %s (attempt=%s)", msg, attempt)
        if attempt >= config.max_retries:
            raise SkipEntryError(f"Too many failures => {url}") from exc
        random_pause(1, 1.5)
        return safe_get(driver, config, url, attempt=attempt + 1)
    except TimeoutException as exc:
        logging.warning("Timeout => attempt=%s, url=%s", attempt, url)
        if attempt >= config.max_retries:
            raise SkipEntryError(f"Timeout x{config.max_retries} => {url}") from exc
        random_pause(1, 1.5)
        return safe_get(driver, config, url, attempt=attempt + 1)
