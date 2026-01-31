from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import ScraperConfig
from .driver import create_driver
from .exceptions import SkipEntryError
from .extract_selenium import parse_phone_email_deep
from .human import do_infinite_scrolling, human_type, random_pause
from .relevance import evaluate_page
from .selenium_ops import click_cookie_consent_if_present, safe_get
from .spec import SearchSpec, render_templates
from .url_filter import is_relevant_url

IMPO_KEYWORDS = ("impressum", "kontakt", "datenschutz", "imprint", "privacy")


def random_synonym_query(name: str, street: str, plz: str, city: str) -> str:
    raw = f"{name} {street} {plz} {city}"
    if random.random() < 0.1:
        raw = raw.replace("straße", "strasse")
    return raw


def link_priority(element: Any) -> int:
    try:
        text = (element.text or "").lower()
        href = (element.get_attribute("href") or "").lower()
        if any(keyword in text or keyword in href for keyword in IMPO_KEYWORDS):
            return 0
    except Exception:
        return 1
    return 1


def search_subpages(
    driver: Any,
    config: ScraperConfig,
    *,
    base_url: str,
    row: dict[str, str],
    spec: SearchSpec,
    max_depth: int,
    query: str,
    attempt: int = 1,
) -> str | None:
    if base_url.lower().endswith(".pdf"):
        logging.info("Skip PDF subpage => %s", base_url)
        return None

    if not safe_get(driver, config, base_url, attempt=attempt):
        return None

    do_infinite_scrolling(driver, max_scroll=3, pause_s=1.2)
    page_source = driver.page_source
    keywords = [k.lower() for k in render_templates(spec.relevance.keyword_templates, row)]
    if evaluate_page(
        page_source,
        keywords=keywords,
        min_keyword_hits=spec.relevance.min_total_keyword_hits,
        require_address=spec.relevance.require_address,
        street=row.get(spec.relevance.address.street_field, ""),
        plz=row.get(spec.relevance.address.zip_field, ""),
        city=row.get(spec.relevance.address.city_field, ""),
        address_min_score=spec.relevance.address.min_score,
    ):
        return base_url

    if max_depth <= 0:
        return None

    visited: set[str] = set()
    max_links = spec.navigation.max_links_per_page
    links = driver.find_elements(By.TAG_NAME, "a")[:max_links]
    links_sorted = sorted(links, key=link_priority)

    for idx, link in enumerate(links_sorted):
        try:
            href = link.get_attribute("href")
        except StaleElementReferenceException as exc:
            logging.warning("Stale subpage BFS => attempt=%s", attempt)
            if attempt >= config.max_retries:
                raise SkipEntryError("subpages => stale => skip") from exc
            links_fresh = driver.find_elements(By.TAG_NAME, "a")[:max_links]
            href = links_fresh[idx].get_attribute("href") if idx < len(links_fresh) else None

        if not href:
            continue
        if href.lower().endswith(".pdf"):
            logging.info("Skip PDF => %s", href)
            continue

        domain = urlparse(href).netloc.lower()
        if domain != urlparse(base_url).netloc.lower():
            continue
        if href in visited:
            continue

        visited.add(href)
        sub_url = search_subpages(
            driver,
            config,
            base_url=href,
            row=row,
            spec=spec,
            max_depth=max_depth - 1,
            query=query,
            attempt=attempt,
        )
        if sub_url is not None:
            return sub_url

    return None


@dataclass
class Session:
    config: ScraperConfig
    driver: Any
    counter: int = 0

    @classmethod
    def create(cls, config: ScraperConfig, *, profile_dir) -> Session:
        return cls(config=config, driver=create_driver(config, profile_dir=profile_dir))

    def close(self) -> None:
        try:
            self.driver.quit()
        except Exception:
            pass

    def maybe_restart_driver(self, *, profile_dir) -> None:
        if self.counter == 0:
            return
        if self.counter % self.config.restart_threshold != 0:
            return

        logging.info("Restart driver => threshold")
        self.close()
        self.driver = create_driver(self.config, profile_dir=profile_dir)

    def search(self, *, query: str, row: dict[str, str], spec: SearchSpec, attempt: int = 1):
        self.maybe_restart_driver(profile_dir=self.config.chrome_profile_root)
        self.counter += 1

        google_url = f"https://www.{self.config.google_domain}/"
        if not safe_get(self.driver, self.config, google_url, attempt=attempt):
            return None, None, None

        random_pause(1, 1.5)
        try:
            click_cookie_consent_if_present(self.driver)
        except Exception:
            pass

        try:
            sb = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, "q")))
        except Exception as exc:
            if attempt >= self.config.max_retries:
                raise SkipEntryError("No search box => skip") from exc
            return None, None, None

        human_type(sb, query)
        random_pause(0.5, 1.0)
        sb.send_keys(Keys.RETURN)
        random_pause(1, 2)

        try:
            WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.ID, "search")))
        except Exception as exc:
            if attempt >= self.config.max_retries:
                raise SkipEntryError("No google results => skip") from exc
            return None, None, None

        do_infinite_scrolling(self.driver, max_scroll=2, pause_s=1.0)
        glinks = self.driver.find_elements(By.XPATH, "//a[contains(@href,'http')]")
        top = glinks[: spec.navigation.max_google_results]
        random.shuffle(top)

        for idx, link in enumerate(top):
            try:
                href = link.get_attribute("href")
            except StaleElementReferenceException as exc:
                if attempt >= self.config.max_retries:
                    raise SkipEntryError(f"stale google link => skip => {exc}") from exc
                glinks_fresh = self.driver.find_elements(By.XPATH, "//a[contains(@href,'http')]")[
                    :20
                ]
                href = glinks_fresh[idx].get_attribute("href") if idx < len(glinks_fresh) else None

            if not href:
                continue
            if href.lower().endswith(".pdf"):
                logging.info("skip pdf => %s", href)
                continue

            if not is_relevant_url(
                query,
                href,
                allowed_tlds=spec.url_filter.allowed_tlds,
                domain_keyword_blacklist=spec.url_filter.domain_keyword_blacklist,
                domain_match=spec.url_filter.domain_match,
                min_query_part_len=spec.url_filter.min_query_part_len,
            ):
                continue

            if not safe_get(self.driver, self.config, href, attempt=attempt):
                continue

            do_infinite_scrolling(self.driver, max_scroll=3, pause_s=1.2)
            ps = self.driver.page_source
            keywords = [k.lower() for k in render_templates(spec.relevance.keyword_templates, row)]
            if evaluate_page(
                ps,
                keywords=keywords,
                min_keyword_hits=spec.relevance.min_total_keyword_hits,
                require_address=spec.relevance.require_address,
                street=row.get(spec.relevance.address.street_field, ""),
                plz=row.get(spec.relevance.address.zip_field, ""),
                city=row.get(spec.relevance.address.city_field, ""),
                address_min_score=spec.relevance.address.min_score,
            ):
                sub_url = None
                if spec.navigation.subpage_depth > 0:
                    sub_url = search_subpages(
                        self.driver,
                        self.config,
                        base_url=href,
                        row=row,
                        spec=spec,
                        max_depth=spec.navigation.subpage_depth,
                        query=query,
                        attempt=attempt,
                    )
                target_url = sub_url or href
                if safe_get(self.driver, self.config, target_url, attempt=attempt):
                    do_infinite_scrolling(self.driver, max_scroll=1, pause_s=1.0)
                    phone, email = None, None
                    if spec.extract_phone or spec.extract_email:
                        phone, email = parse_phone_email_deep(self.driver)
                        if not spec.extract_phone:
                            phone = None
                        if not spec.extract_email:
                            email = None
                    return target_url, phone, email

            if random.random() < 0.7:
                self.driver.back()
                random_pause(0.7, 1.5)

        return None, None, None
