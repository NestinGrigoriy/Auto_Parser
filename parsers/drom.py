import time
import random
import re
from selenium.webdriver.common.by import By
from core.base_parser import BaseParser
from core.enums import City
from core.models import SearchConfig, CarItem


class DromParser(BaseParser):
    REGION_MAP = {
        City.MOSCOW: "region77",
        City.SPB: "region78",
        City.KRASNODAR: "region23",
        City.EKATERINBURG: "region66",
        City.NOVOSIBIRSK: "region54",
        City.VLADIVOSTOK: "region25",
        City.KAZAN: "region16"
    }

    def _build_url(self, config: SearchConfig, page: int) -> str:
        base = "https://auto.drom.ru"
        region = self.REGION_MAP.get(config.city, "")
        url = f"{base}/{region}/{config.brand}/{config.model}/"
        if page > 1:
            url += f"page{page}/"

        params = ["ph=1", "unsold=1"]
        if config.min_price: params.append(f"minprice={config.min_price}")
        if config.max_price: params.append(f"maxprice={config.max_price}")
        if config.min_year: params.append(f"minyear={config.min_year}")
        if config.max_km: params.append(f"maxprobeg={config.max_km}")
        if config.radius: params.append(f"distance={config.radius}")

        return url + "?" + "&".join(params)

    def parse(self, config: SearchConfig) -> list[CarItem]:
        self._init_driver()
        results = []

        try:
            for page in range(1, config.max_pages + 1):
                url = self._build_url(config, page)
                print(f"[DROM] Страница {page}: {url}")
                self.driver.get(url)
                time.sleep(random.uniform(3, 5))

                # Карточки объявлений
                ads = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-ftid="bulls-list_bull"]')

                for ad in ads:
                    try:
                        # Основные элементы
                        title_el = ad.find_element(By.CSS_SELECTOR, 'a[data-ftid="bull_title"]')
                        price_el = ad.find_element(By.CSS_SELECTOR, 'span[data-ftid="bull_price"]')
                        link = title_el.get_attribute("href")
                        full_text = ad.text  # Берем весь текст карточки для поиска Regex

                        # --- 1. ПАРСИНГ ГОДА ---
                        # Обычно в заголовке: "BMW X5, 2019"
                        title_text = title_el.text
                        year_match = re.search(r'\b(19|20)\d{2}\b', title_text)
                        year = int(year_match.group(0)) if year_match else 0

                        # --- 2. ПАРСИНГ ПРОБЕГА ---
                        # Ищем "100 000 км" во всем тексте карточки
                        km_int = 0
                        km_str = "-"
                        km_match = re.search(r'(\d[\d\s]*)\s?км', full_text)

                        if km_match:
                            clean_km = km_match.group(1).replace(" ", "")
                            if clean_km.isdigit():
                                km_int = int(clean_km)
                                km_str = f"{km_int} км"

                        # --- 3. ПАРСИНГ ГОРОДА ---
                        # Чтобы не было City.EKATERINBURG, парсим реальный город из объявления
                        try:
                            loc_el = ad.find_element(By.CSS_SELECTOR, 'span[data-ftid="bull_location"]')
                            location = loc_el.text
                        except:
                            # Fallback: если не нашли, берем из конфига значение (value), а не сам Enum
                            location = config.city.value

                        # --- 4. ЖЕСТКАЯ ФИЛЬТРАЦИЯ ---
                        # Дром иногда подмешивает машины из других регионов или "под заказ"
                        if config.max_km and km_int > config.max_km and km_int > 0:
                            continue
                        if config.min_year and year < config.min_year and year > 0:
                            continue

                        item = CarItem(
                            source="drom",
                            title=title_text,
                            price=self._clean_price(price_el.text),
                            year=year,
                            km=km_str,
                            link=link,
                            location=location
                        )
                        results.append(item)
                    except Exception:
                        continue

                print(f"   [DROM] Валидных авто: {len(results)}")

        finally:
            self.cleanup()

        return results