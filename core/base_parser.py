import random
from abc import ABC, abstractmethod
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from .models import SearchConfig, CarItem

class BaseParser(ABC):
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None

    def _get_chrome_options(self) -> Options:
        options = webdriver.ChromeOptions()
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        if self.headless:
            options.add_argument("--headless")
        return options

    def _init_driver(self):
        if not self.driver:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self._get_chrome_options()
            )
            # Скрипт для скрытия Selenium (из avito.py)
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })

    def _clean_price(self, text: str) -> int:
        """Универсальная очистка цены для всех парсеров"""
        try:
            digits = ''.join(filter(str.isdigit, text))
            return int(digits) if digits else 0
        except:
            return 0

    def cleanup(self):
        if self.driver:
            self.driver.quit()

    @abstractmethod
    def parse(self, config: SearchConfig) -> List[CarItem]:
        """Этот метод должен быть реализован в каждом парсере"""
        pass
