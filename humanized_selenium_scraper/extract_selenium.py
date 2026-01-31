from __future__ import annotations

import re
from typing import Any

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from .extract_text import (
    decode_antispam_mail,
    parse_less_generous_phones,
    parse_phone_and_email_obfuscated,
)


def _parse_meta_tags(driver: Any) -> str:
    metas = driver.find_elements(By.TAG_NAME, "meta")
    lines: list[str] = []
    for meta in metas:
        content = meta.get_attribute("content") or ""
        if content.strip():
            lines.append(content.strip())
    return "\n".join(lines)


def _parse_hidden_inputs(driver: Any) -> str:
    hiddens = driver.find_elements(By.CSS_SELECTOR, "input[type='hidden']")
    values: list[str] = []
    for hidden in hiddens:
        value = hidden.get_attribute("value") or ""
        if value.strip():
            values.append(value.strip())
    return "\n".join(values)


def parse_phone_email_deep(driver: Any) -> tuple[str | None, str | None]:
    page_src = driver.page_source
    meta_txt = _parse_meta_tags(driver)
    hidden_txt = _parse_hidden_inputs(driver)
    combined = "\n".join([page_src, meta_txt, hidden_txt])

    phone_set: set[str] = set()
    mail_set: set[str] = set()

    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        try:
            href = link.get_attribute("href") or ""
            txt = link.text or ""

            if href.lower().startswith("tel:"):
                candidate = href[4:].strip()
                if len(re.sub(r"\D", "", candidate)) >= 7:
                    phone_set.add(candidate)
            elif href.lower().startswith("mailto:"):
                mail_set.add(href[7:].strip())
            elif "linkdecrypt" in href.lower():
                encs = re.findall(r"linkDecrypt\('([^']+)'\)", href, re.IGNORECASE)
                for enc in encs:
                    dec = decode_antispam_mail(enc)
                    if dec.startswith("mailto:"):
                        mail_set.add(dec[7:].strip())

            if "telefon:" in txt.lower() or "tel." in txt.lower():
                phone_set.update({p.strip() for p in parse_less_generous_phones(txt)})
        except StaleElementReferenceException:
            continue

    phs, ems = parse_phone_and_email_obfuscated(combined)
    phone_set.update({p.strip() for p in phs})
    mail_set.update({e.strip() for e in ems})

    phone = next(iter(phone_set), None)
    email = next(iter(mail_set), None)
    return phone, email
