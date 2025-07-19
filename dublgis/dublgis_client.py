import os
import requests
from bs4 import BeautifulSoup
from random import randrange


class DublGISClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = "https://catalog.api.2gis.com/3.0"

    def _clean_text(self, text: str) -> str:
        return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)

    def _get_json(self, url: str) -> dict | None:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def _get_city_id(self, city: str) -> str | None:
        url = f'{self.base_url}/items?q="{city}"&key={self.api_key}'
        data = self._get_json(url)
        try:
            return data["result"]["items"][0]["id"]
        except (KeyError, IndexError, TypeError):
            return None

    def _get_interesting_place_id(self, city_id: str) -> str | None:
        url = (
            f'{self.base_url}/items?q=достопримечательности'
            f"&fields=items.point&city_id={city_id}&key={self.api_key}"
        )
        data = self._get_json(url)
        try:
            items = data["result"]["items"]
            if not items:
                return None
            return items[randrange(len(items))]["id"]
        except (KeyError, IndexError, TypeError):
            return None

    def get_place_info(self, place_id: str) -> tuple[str, str] | None:
        url = f"{self.base_url}/items/byid?id={place_id}&fields=items.links&key={self.api_key}"
        data = self._get_json(url)
        try:
            item = data["result"]["items"][0]
            name = self._clean_text(item["full_name"])
            description = self._clean_text(item["links"]["attractions"][0]["description"])
            return name, description
        except (KeyError, IndexError, TypeError):
            return None

    def get_random_place_in_city_info(self, city: str) -> tuple[str, str] | None:
        city_id = self._get_city_id(city)
        if not city_id:
            print(f"City ID: {city_id}")
            return None
        place_id = self._get_interesting_place_id(city_id)
        if not place_id:
            print(f"Place ID: {place_id}")
            return None
        return self.get_place_info(place_id)
    
