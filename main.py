import openai
import requests

import json

from random import randrange
from dotenv import dotenv_values

config = dotenv_values(".env")

openai.api_key = config['openai_key']
openai.base_url = config['openai_ip']
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

    # Проверяем, что запрос успешен (статус код 200)
    if response.status_code == 200:
        # Получаем JSON из ответа
        json_data = response.json()
    return json_data

def get_info(city):
    search_city_url = f'https://catalog.api.2gis.com/3.0/items?q={city}&key={dublgis_key}'
    city_ind = get_json(search_city_url)["result"]["items"][0]["id"]

    search_pl_url = f'https://catalog.api.2gis.com/3.0/items?q=достопримечательности&fields=items.point&city_id={city_ind}&key={dublgis_key}'
    interensting_places = get_json(search_pl_url)["result"]["items"]
    place_ids = [x["id"] for x in interensting_places]
    place_id = place_ids[randrange(len(place_ids))]

    place_info_url = f'https://catalog.api.2gis.com/3.0/items/byid?id={place_id}&key={dublgis_key}&fields=items.description'
    place_info_json = get_json(place_info_url)["result"]["items"][0]
    print(place_info_json)
    place_info = place_info_json["description"]
    place_name = place_info_json["full_name"]
    return place_name, place_info





def gen_mystery():
    city = cities[randrange(len(cities))]
    place, description = get_info(city)
    print(place, description)
    # SYSTEM_PROMPT = f"""
    # Ты — ассистент, поддерживающий диалог с пользователем.
    # Тебе надо загадать загадку про объект культуры. 
    # Вот его название: {place}
    # А вот его описание: {description} 

    # Если пользователь хочет начать заново (написал что-то вроде "по новой", "заново", "начнём сначала", "сбрось" и т.п.),
    # ответь в JSON-формате:
    # {"reset": true, "reply": "Хорошо, начинаем с начала!"}

    # Если пользователь продолжает разговор, ответь в формате:
    # {"reset": false, "reply": "Твой ответ..."}

    # Всегда возвращай ответ строго в JSON.
    # """


# chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]

def call_llm():
    response = openai.ChatCompletion.create(
        model="Qwen/Qwen3-32B",  
        messages=chat_history,
        temperature=0.7,
        max_tokens=512
    )
    return response['choices'][0]['message']['content']

def handle_user_input(user_input: str):
    global chat_history

    chat_history.append({"role": "user", "content": user_input})
    raw_response = call_llm()

    try:
        data = json.loads(raw_response)
        if not isinstance(data, dict) or "reset" not in data or "reply" not in data:
            raise ValueError("Неверный формат")

        if data["reset"]:
            chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
            return data["reply"]

        chat_history.append({"role": "assistant", "content": data["reply"]})
        return data["reply"]

    except Exception:
        chat_history.append({"role": "assistant", "content": raw_response})
        return raw_response

def chat_loop():
    print("💬 Чат с vLLM запущен. Напишите 'по новой' или что-то подобное для сброса. Ctrl+C — выход.\n")
    try:
        while True:
            user_input = input("Вы: ").strip()
            if not user_input:
                continue
            reply = handle_user_input(user_input)
            print(f"Ассистент: {reply}\n")
    except KeyboardInterrupt:
        print("\n🛑 Выход из чата.")

if __name__ == "__main__":
    # chat_loop()
    gen_mystery()

    