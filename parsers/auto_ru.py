import time
from selenium.webdriver.common.by import By
from core.base_parser import BaseParser
from core.enums import City
from core.models import SearchConfig, CarItem


class AutoRuParser(BaseParser):
    city_map = {
        City.MOSCOW: "moskva",
        City.SPB: "sankt-peterburg",
        City.KRASNODAR: "krasnodar",
        City.EKATERINBURG: "ekaterinburg",
        City.NOVOSIBIRSK: "novosibirsk",
        City.VLADIVOSTOK: "vladivostok",
        City.KAZAN: "kazan"
    }

    def _build_url(self, config: SearchConfig, page: int) -> str:
        city = self.city_map.get(config.city, "moskva")

        base = f"https://auto.ru/{city}/cars/{config.brand}/{config.model}/all/"

        params = []
        if config.min_price:
            params.append(f"price_from={config.min_price}")
        if config.max_price:
            params.append(f"price_to={config.max_price}")
        if config.min_year:
            params.append(f"year_from={config.min_year}")
        if page > 1: params.append(f"page={page}")

        if config.max_km:
            params.append(f"km_to={config.max_km}")
        if config.radius:
            params.append(f"geo_radius={config.radius}")

        if page > 1:
            params.append(f"page={page}")

        if params:
            base += "?" + "&".join(params)
        return base

    def parse(self, config: SearchConfig) -> list[CarItem]:
        self._init_driver()
        results = []

        try:
            for page in range(1, config.max_pages + 1):
                url = self._build_url(config, page)
                self.driver.get(url)
                time.sleep(5)

                if "SmartCaptcha" in self.driver.page_source:
                    print("⚠️ [AUTO.RU] КАПЧА! Решите вручную за 45 сек...")
                    time.sleep(45)

                for _ in range(3):
                    self.driver.execute_script("window.scrollBy(0, 800);")
                    time.sleep(1)

                link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/cars/'][href*='/sale/']")

                seen_urls = set()

                for link_el in link_elements:
                    try:
                        href = link_el.get_attribute("href")
                        if not href or href in seen_urls or "new" in href:
                            continue
                        seen_urls.add(href)

                        try:
                            parent = link_el.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ListingItem')]")
                        except:
                            continue

                        price = 0
                        price_selectors = [
                            "[class*='Price-module__price']",
                            "[class*='price-module__price']",
                            "[class*='ListingItemPrice-module__content']"
                        ]

                        for selector in price_selectors:
                            try:
                                price_el = parent.find_element(By.CSS_SELECTOR, selector)
                                price_text = price_el.text
                                clean_p = self._clean_price(price_text)
                                if clean_p > 1000:
                                    price = clean_p
                                    break
                            except:
                                continue

                        if price == 0:
                            try:
                                full_text = parent.text
                                for line in full_text.split('\n'):
                                    if '₽' in line:
                                        p = self._clean_price(line)
                                        if p > 100000:
                                            price = p
                                            break
                            except:
                                pass

                        full_text = parent.text
                        year = 0
                        km = "-"

                        for line in full_text.split('\n'):
                            if line.isdigit() and len(line) == 4 and (line.startswith("19") or line.startswith("20")):
                                year = int(line)
                            if "км" in line:
                                km = line

                        item = CarItem(
                            source="auto.ru",
                            title=link_el.text or f"{config.brand} {config.model}",
                            price=price,
                            year=year,
                            km=km,
                            link=href,
                            location=self.city_map.get(config.city)
                        )
                        results.append(item)

                    except Exception as e:
                        continue

        except Exception as e:
            print(f"[AUTO.RU] Критическая ошибка: {e}")
        finally:
            self.cleanup()

        return results