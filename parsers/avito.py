import time
import random
import re
from selenium.webdriver.common.by import By
from core.base_parser import BaseParser
from core.models import SearchConfig, CarItem
from core.enums import City


class AvitoParser(BaseParser):
    CITY_MAP = {
        City.MOSCOW: "moskva",
        City.SPB: "sankt-peterburg",
        City.KRASNODAR: "krasnodar",
        City.EKATERINBURG: "ekaterinburg",
        City.NOVOSIBIRSK: "novosibirsk",
        City.VLADIVOSTOK: "vladivostok",
        City.KAZAN: "kazan"
    }

    def _build_url(self, config: SearchConfig, page: int) -> str:
        query = f"{config.brand} {config.model}"
        city_slug = self.CITY_MAP.get(config.city, "rossiya")
        base_url = f"https://www.avito.ru/{city_slug}/avtomobili"

        params = [f"q={query}", "s=104"]
        if page > 1: params.append(f"p={page}")
        if config.max_price: params.append(f"pmax={config.max_price}")
        if config.min_price: params.append(f"pmin={config.min_price}")
        if config.radius: params.append(f"radius={config.radius}")

        return f"{base_url}?" + "&".join(params)

    def parse(self, config: SearchConfig) -> list[CarItem]:
        self._init_driver()
        results = []

        try:
            for page in range(1, config.max_pages + 1):
                url = self._build_url(config, page)
                print(f"[AVITO] Стр. {page}...")
                self.driver.get(url)

                # Скролл
                for _ in range(random.randint(2, 4)):
                    self.driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
                    time.sleep(0.5)
                time.sleep(3)

                items = self.driver.find_elements(By.CSS_SELECTOR, "[data-marker='item']")

                for item in items:
                    try:
                        title_el = item.find_element(By.CSS_SELECTOR, "[data-marker='item-title']")
                        price_el = item.find_element(By.CSS_SELECTOR, "[data-marker='item-price']")

                        title_text = title_el.text
                        price = self._clean_price(price_el.text)
                        link = title_el.get_attribute("href")

                        # --- ПАРСИНГ ИЗ ЗАГОЛОВКА ---
                        # Пример: "BMW X5, 2019, 153 165 км"

                        # 1. Год
                        year_match = re.search(r'\b(19|20)\d{2}\b', title_text)
                        year = int(year_match.group(0)) if year_match else 0

                        # 2. Пробег (ищем "число км" в заголовке или описании)
                        km_int = 0
                        # Пробуем вытащить цифры перед "км"
                        km_match = re.search(r'(\d[\d\s]*)\s?км', title_text)
                        if km_match:
                            clean_km = km_match.group(1).replace(" ", "").replace("\xa0", "")
                            if clean_km.isdigit():
                                km_int = int(clean_km)

                        if config.max_km and km_int > config.max_km and km_int > 0:
                            continue
                        if config.min_year and year < config.min_year and year > 0:
                            continue

                        # Локация
                        try:
                            loc_el = item.find_element(By.CSS_SELECTOR, "[class*='geo-root']")
                            location = loc_el.text
                        except:
                            location = "-"

                        car = CarItem(
                            source="avito",
                            title=title_text,
                            price=price,
                            year=year,
                            km=f"{km_int} км",
                            link=link,
                            location=location
                        )
                        results.append(car)
                    except Exception:
                        continue

                print(f"   [AVITO] Валидных авто: {len(results)}")

        except Exception as e:
            print(f"[AVITO] Ошибка: {e}")
        finally:
            self.cleanup()

        return results