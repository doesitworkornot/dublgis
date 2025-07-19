import json
import requests
from random import randrange
from dotenv import dotenv_values


from model.model_client import Model


config = dotenv_values(".env")
dublgis_key = config['dublgis']

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
    "Уфа"
]

def get_json(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_info(city):
    search_city_url = f'https://catalog.api.2gis.com/3.0/items?q={city}&key={dublgis_key}'
    city_ind = get_json(search_city_url)["result"]["items"][0]["id"]

    search_pl_url = f'https://catalog.api.2gis.com/3.0/items?q=достопримечательности&fields=items.point&city_id={city_ind}&key={dublgis_key}'
    interensting_places = get_json(search_pl_url)["result"]["items"]
    place_ids = [x["id"] for x in interensting_places]
    place_id = place_ids[randrange(len(place_ids))]

    place_info_url = f'https://catalog.api.2gis.com/3.0/items/byid?id={place_id}&key={dublgis_key}&fields=items.description'
    place_info_json = get_json(place_info_url)["result"]["items"][0]
    place_info = place_info_json["description"]
    place_name = place_info_json["full_name"]
    return place_name, place_info

def gen_mystery():
    city = cities[randrange(len(cities))]
    place, description = get_info(city)
    return place, description

def chat_loop():
    print("Чат с vLLM запущен. Напишите 'по новой' или что-то подобное для сброса. Ctrl+C — выход.\n")
    model = Model()
    user_id = "default_user"  # In a real app, use a unique user/session id
    place, description = gen_mystery()
    print(f"Загадано место: {place}\nОписание: {description}\n")  # For debug, remove in prod
    try:
        while True:
            user_input = input("Вы: ").strip()
            if not user_input:
                continue
            if user_input.lower() in [
                "по новой", "заново", "начнём сначала", "сбрось", "reset", "start over"
            ]:
                model.reset(user_id)
                print("Ассистент: Хорошо, начинаем с начала!\n")
                place, description = gen_mystery()
                print(f"Загадано место: {place}\nОписание: {description}\n")  # For debug, remove in prod
                continue
            reply = model.ask(user_id, user_input)
            print(f"Ассистент: {reply}\n")
    except KeyboardInterrupt:
        print("\nВыход из чата.")

if __name__ == "__main__":
    chat_loop()

    