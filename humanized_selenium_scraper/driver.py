from __future__ import annotations

import os
import random
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from .config import ScraperConfig


def create_driver(config: ScraperConfig, *, profile_dir: Path) -> webdriver.Chrome:
    user_agent = random.choice(config.user_agents)
    width, height = random.choice(config.window_sizes)

    chrome_opts = Options()
    os.makedirs(profile_dir, exist_ok=True)
    chrome_opts.add_argument(f"--user-data-dir={profile_dir}")
    chrome_opts.add_argument(f"--user-agent={user_agent}")
    chrome_opts.add_argument(f"--window-size={width},{height}")

    driver = webdriver.Chrome(service=Service(), options=chrome_opts)
    driver.set_page_load_timeout(config.page_load_timeout_s)
    driver.implicitly_wait(config.implicit_wait_s)
    return driver
