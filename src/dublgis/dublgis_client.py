import os
import requests
from bs4 import BeautifulSoup
from random import choice
from PIL import Image


cities = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Челябинск",
    "Самара",
    "Ростов-на-Дону",
    "Уфа",
]


class DublGISClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("DGIS_API_KEY")
        self.base_url = "https://catalog.api.2gis.com/3.0"

    def _clean_text(self, text: str) -> str:
        return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)

    def _get_json(self, url: str, params: dict) -> dict | None:
        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            return None

    def _get_city_id(self, city: str) -> str | None:
        url = f"{self.base_url}/items"
        params = {"q": city, "key": self.api_key}
        data = self._get_json(url, params)
        try:
            return data["result"]["items"][0]["id"]
        except Exception:
            return None

    def _get_interesting_place_id(self, city_id: str) -> str | None:
        url = f"{self.base_url}/items"
        params = {
            "type": "attraction",
            "city_id": city_id,
            "fields": "items.description",
            "key": self.api_key,
        }
        data = self._get_json(url, params)
        try:
            items = data["result"]["items"]
            long_desc_items = []
            for item in items:
                raw = item.get("description")
                if not raw:
                    continue
                text = self._clean_text(raw)
                if len(text.split()) > 15:
                    long_desc_items.append(item)
            if not long_desc_items:
                return None
            selected = choice(long_desc_items)
            return selected["id"]
        except Exception:
            return None

    def get_place_image_url(self, place_id: str) -> Image:
        response = requests.get(
            f"{self.base_url}/items/byid?id={place_id}&fields=items.description,items.external_content&key=4f1cf2d3-6572-4f77-8e19-fc9a65b5af05"
        )
        response.json()

        image_url = requests.get(
            response.json()["result"]["items"][0]["external_content"][0][
                "main_photo_url"
            ],
            stream=True,
        ).raw

        return image_url

    def get_place_info(self, place_id: str) -> tuple[str, str] | None:
        url = f"{self.base_url}/items/byid"
        params = {
            "id": place_id,
            "fields": "items.full_name,items.description",
            "key": self.api_key,
        }
        data = self._get_json(url, params)
        try:
            item = data["result"]["items"][0]
            name = self._clean_text(item["full_name"])
            desc = self._clean_text(item.get("description", ""))
            return name, desc
        except Exception:
            return None

    def get_random_place_in_city_info(self) -> tuple[str, str, str]:
        while True:
            city = choice(cities)
            city_id = self._get_city_id(city)
            if not city_id:
                continue
            place_id = self._get_interesting_place_id(city_id)
            if not place_id:
                continue
            info = self.get_place_info(place_id)
            if info:
                name, desc = info
                return city, name, desc
