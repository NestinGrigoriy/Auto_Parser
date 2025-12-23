import csv
from typing import List
from core.models import CarItem


def save_to_csv(data: List[CarItem], filename: str = "report.csv"):
    if not data:
        print("Нет данных для сохранения.")
        return

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        headers = ["Источник", "Авто", "Цена", "Год", "Пробег", "Город", "Ссылка"]
        writer.writerow(headers)

        for item in data:
            writer.writerow([
                item.source,
                item.title,
                item.price,
                item.year,
                item.km,
                item.location,
                item.link
            ])
    print(f"💾 Файл {filename} успешно сохранен ({len(data)} записей).")
