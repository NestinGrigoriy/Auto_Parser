from dataclasses import dataclass
from typing import Optional

from core.enums import City


@dataclass
class SearchConfig:
    brand: str
    model: str
    city: City = City.SPB
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_year: Optional[int] = None
    max_pages: int = 1

    max_km: Optional[int] = None
    radius: Optional[int] = None

@dataclass
class CarItem:
    source: str             # "avito", "drom", "auto.ru"
    title: str
    price: int
    year: int
    km: str
    link: str
    location: City | str
    description: str = ""