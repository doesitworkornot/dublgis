import sys
from dotenv import dotenv_values


from model.model_client import Model
from dublgis.dublgis_client import DublGISClient
from predict_model.model import Predictor


def safe_input(prompt):
    try:
        return input(prompt)
    except UnicodeDecodeError:
        print("\n[!] Проблема с кодировкой. Введите строку ещё раз:")
        return sys.stdin.buffer.readline().decode("utf-8").strip()


config = dotenv_values(".env")
dublgis_key = config["dublgis"]


def chat_loop(level=1):
    print(
        "Чат запущен. Напишите 'по новой' или что-то подобное для сброса. Ctrl+C — выход.\n"
    )
    model_client = Model(config["openai_key"])
    model_predict = Predictor(config["openai_key"])
    dublgis_client = DublGISClient(config["dublgis"])
    user_id = "default_user"
    city, place, description = dublgis_client.get_random_place_in_city_info()

    output = f"Загадано место: {place}\nОписание: {description}\n"
    print(output)
    greeting = model_client.init_conv(city, place, description, user_id)
    model_predict.remember_assistant(
        user_id, f"Загадано место: {place}\nОписание: {description}\n"
    )

    print(f"Ассистент: {greeting}")
    try:
        while True:
            user_input = safe_input("Вы: ").strip()
            if not user_input:
                continue

            prediction = model_predict.predict(user_id, user_input)
            print(f"SYTEM PREDICTION: {prediction}")

            if prediction == "RESET":
                reply = model_client.reset(user_id)
                print(f"Ассистент: {reply}\n")
                model_client.reset(user_id)
                model_predict.reset(user_id)
                city, place, description = (
                    dublgis_client.get_random_place_in_city_info()
                )
                greeting = model_client.init_conv(city, place, description, user_id)
                print(f"Загадано место: {place}\nОписание: {description}\n")
                print(greeting)
                continue

            if prediction == "CORRECT":
                reply = model_client.reset(user_id)
                model_predict.reset(user_id)
                print(f"Ассистент: {reply}\n")
                city, place, description = (
                    dublgis_client.get_random_place_in_city_info()
                )
                greeting = model_client.init_conv(city, place, description, user_id)
                print(f"Загадано место: {place}\nОписание: {description}\n")
                print(greeting)
                continue

            reply = model_client.ask(user_id, user_input)
            model_predict.remember_assistant(user_id, reply)
            print(f"Ассистент: {reply}\n")
    except KeyboardInterrupt:
        print("\nВыход из чата.")


if __name__ == "__main__":
    chat_loop(level=1)
