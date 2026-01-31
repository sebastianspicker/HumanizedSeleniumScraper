from __future__ import annotations

import random
import time


def human_type(element, text: str) -> None:
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.3))


def random_pause(base_s: float = 1.0, var_s: float = 2.0) -> None:
    time.sleep(base_s + random.random() * var_s)


def do_infinite_scrolling(driver, max_scroll: int = 3, pause_s: float = 1.0) -> None:
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_s)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
