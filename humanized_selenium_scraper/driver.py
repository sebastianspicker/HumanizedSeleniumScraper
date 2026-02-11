from __future__ import annotations

import os
import random
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from .config import ScraperConfig


def create_driver(config: ScraperConfig, *, profile_dir: Path) -> webdriver.Chrome:
    user_agents = config.user_agents or [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    ]
    window_sizes = config.window_sizes or [(1280, 720)]
    user_agent = random.choice(user_agents)
    width, height = random.choice(window_sizes)

    chrome_opts = Options()
    os.makedirs(profile_dir, exist_ok=True)
    chrome_opts.add_argument(f"--user-data-dir={profile_dir}")
    chrome_opts.add_argument(f"--user-agent={user_agent}")
    chrome_opts.add_argument(f"--window-size={width},{height}")

    driver = webdriver.Chrome(service=Service(), options=chrome_opts)
    driver.set_page_load_timeout(config.page_load_timeout_s)
    driver.implicitly_wait(config.implicit_wait_s)
    return driver
