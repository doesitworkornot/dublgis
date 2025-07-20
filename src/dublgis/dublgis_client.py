import os
import requests
from bs4 import BeautifulSoup
from random import choice
from typing import Optional


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
        self.current_place_id = None
        self.city_id = None

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
            self.city_id = data["result"]["items"][0]["id"]
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

    def get_place_image_url(self, place_id=None) -> str | None:
        if place_id is None:
            place_id = self.current_place_id
        try:
            response = requests.get(
                f"{self.base_url}/items/byid?id={place_id}"
                "&fields=items.description,items.external_content"
                f"&key={self.api_key}"
            )
            return response.json()["result"]["items"][0]["external_content"][0][
                "main_photo_url"
            ]
        except Exception:
            return None

    def get_browser_link(self, place_id: Optional[str] = None) -> str:
        place_id = place_id or self.current_place_id
        city_part = self.city_id or "geo"
        return f"https://2gis.ru/{city_part}/firm/{place_id}"

    def get_nearby_places(
        self,
        lat: float,
        lon: float,
        logger,
        radius: int = 2000,
        limit: int = 10,
    ) -> list[dict]:
        query = "кафе, ресторан, достопримечательность, университет, вуз, торговый центр, бизнес-центр, храм, церковь, мечеть, музей, театр, галерея"

        url = f"{self.base_url}/items"
        params = {
            "q": query,
            "point": f"{lon},{lat}",
            "radius": radius,
            "sort": "distance",
            "page_size": 10,
            "type": "branch",
            "fields": "items.point,items.reviews,items.links,items.media,items.description",
            "key": self.api_key,
        }

        data = self._get_json(url, params)
        logger.info(f"DATA: {data}")
        if not data:
            return []

        results = []
        for item in data["result"]["items"]:
            logger.info(f"ITEM: {item}")
            if item["id"] == self.current_place_id:
                continue

            results.append(
                {
                    "name": self._clean_text(item["name"]),
                    "description": self._clean_text(item.get("description", "")),
                    "rating": item.get("reviews", {}).get("general_rating"),
                    "reviews_link": f"{self.get_browser_link(item['id'])}/tab/reviews",
                    "inside": f"{self.get_browser_link(item['id'])}/tab/inside",
                    "object_link": self.get_browser_link(item["id"]),
                    "image_url": self.get_place_image_url(item["id"]),
                }
            )

            logger.info(f"RESULTS: {results}")
            if len(results) >= limit:
                break

        return results

    def get_place_info(self, place_id: str) -> tuple[str, str, float, float] | None:
        url = f"{self.base_url}/items/byid"
        params = {
            "id": place_id,
            "fields": "items.full_name,items.description,items.point",
            "key": self.api_key,
        }
        data = self._get_json(url, params)
        try:
            item = data["result"]["items"][0]
            name = self._clean_text(item["full_name"])
            desc = self._clean_text(item.get("description", ""))
            lat = item["point"]["lat"]
            lon = item["point"]["lon"]
            return name, desc, lat, lon
        except Exception:
            return None

    def get_random_place_in_city_info(self) -> tuple[str, str, str, float, float]:
        while True:
            city = choice(cities)
            city_id = self._get_city_id(city)
            if not city_id:
                continue
            place_id = self._get_interesting_place_id(city_id)
            if not place_id:
                continue
            self.current_place_id = place_id
            info = self.get_place_info(place_id)
            if info:
                name, desc, lat, lon = info
                return city, name, desc, lat, lon
