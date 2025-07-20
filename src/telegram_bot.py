import os
import html
import logging
from dotenv import dotenv_values
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


from model.model_client import Model
from dublgis.dublgis_client import DublGISClient
from predict_model.model import Predictor

config = dotenv_values(".env")

TELEGRAM_TOKEN = config["telegram_token"]
OPENAI_KEY = config["openai_key"]
DUBLGIS_KEY = config["dublgis"]

model_client = Model(OPENAI_KEY)
model_predict = Predictor(OPENAI_KEY)
dublgis_client = DublGISClient(DUBLGIS_KEY)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)


def get_user_logger(user_id: str) -> logging.Logger:
    logger_name = f"user_{user_id}"
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        os.makedirs("logs", exist_ok=True)
        fh = logging.FileHandler(
            os.path.join("logs", f"{user_id}.log"), encoding="utf-8"
        )
        fh.setFormatter(logging.Formatter("%(asctime)s — %(message)s"))
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def new_round(user_id: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    city, place, description, lat, lon = dublgis_client.get_random_place_in_city_info()
    context.user_data.update(
        city=city, place=place, description=description, lat=lat, lon=lon
    )

    system_msg = f"Загадано место: {place}\nОписание: {description}"
    user_logger = get_user_logger(user_id)
    user_logger.info("=== NEW ROUND ===")
    user_logger.info(system_msg)

    model_predict.remember_assistant(user_id, system_msg)
    greeting = model_client.init_conv(city, place, description, user_id)

    user_logger.info(f"MODEL GREETING: {greeting}")
    return greeting


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    greeting = new_round(user_id, context)
    await update.message.reply_text(greeting)


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_logger = get_user_logger(user_id)

    user_logger.info("CMD: /reset")
    reply = model_client.reset(user_id)
    model_predict.reset(user_id)
    user_logger.info(f"MODEL RESET REPLY: {reply}")

    await update.message.reply_text("Диалог перезапущен.")
    greeting = new_round(user_id, context)
    await update.message.reply_text(greeting)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_id = str(update.effective_user.id)
    user_logger = get_user_logger(user_id)

    user_input = update.message.text.strip()
    user_logger.info(f"USER: {user_input}")

    reply = model_client.ask(user_id, user_input)
    model_predict.remember_assistant(user_id, reply)

    prediction = model_predict.predict(user_id, user_input)
    user_logger.info(f"PREDICTOR: {prediction}")

    if prediction in ("RESET", "CORRECT"):
        place = context.user_data.get("place")
        lon = context.user_data.get("lon")
        lat = context.user_data.get("lat")
        user_logger.info(f"place: {place}")

        reply = model_client.bid_farewell(user_id)
        model_predict.reset(user_id)

        user_logger.info(f"MODEL RESET REPLY: {reply}")
        image_url = dublgis_client.get_place_image_url()
        link = html.escape(dublgis_client.get_browser_link(dublgis_client.current_place_id), quote=True)
        reply_with_link = (
            f"{reply}\n<a href=\"{link}\">Ссылка на место в 2ГИС</a>"
        )

        if image_url:
            await update.message.reply_photo(
                photo=image_url, caption=reply_with_link, parse_mode="HTML"
            )
        else:
            await update.message.reply_text(reply_with_link, parse_mode="HTML")

        if place and lon and lat:
            nearby_place = dublgis_client.get_nearby_places(lat, lon, user_logger)[0]
            user_logger.info(f"nearby_places: {nearby_place}")
            result_to_model = [
                {
                    "name": nearby_place["name"],
                    "description": nearby_place["description"],
                    "rating": nearby_place["rating"],
                }
            ]
            img_url = nearby_place["image_url"]
            place_url = nearby_place["object_link"]
            reply = model_client.recommmend(user_id, result_to_model)
            reply += f'\nВот <a href="{place_url}">ссылка на это место</a>, если тебе интересно.'

            if img_url:
                await update.message.reply_photo(
                    photo=img_url, caption=reply, parse_mode="HTML"
                )
            else:
                await update.message.reply_text(reply, parse_mode="HTML")
        model_client.reset(user_id)
        greeting = new_round(user_id, context)
        await update.message.reply_text(greeting)
        return

    remaining = model_client.max_attempts - model_client.memory.attempts_count
    if remaining <= 5:
        description = context.user_data.get("description")
        image_url = dublgis_client.get_place_image_url()
        user_logger.info(f"REMAINING ATTEMPTS: {remaining}")

        if description:
            hint = model_client.get_hint_from_description(description, user_id)
            user_logger.info(f"HINT: {hint}")

            caption = (
                f"<b>Подсказка!</b>\n"
                f"Осталось <b>{remaining}</b> попыток.\n\n"
                f"{hint}"
            )
            if image_url:
                await update.message.reply_photo(
                    photo=image_url, caption=caption, parse_mode="HTML"
                )
            else:
                await update.message.reply_text(caption, parse_mode="HTML")
    if remaining == 0:
        reply = model_client.reset(user_id)
        model_predict.reset(user_id)

        link = html.escape(dublgis_client.get_browser_link(dublgis_client.current_place_id), quote=True)
        reply_text = (
            "Попытки исчерпаны, и не удалось получить подсказку.<br>"
            f"Вот правильный ответ:<br><br>{reply}<br>"
            f'<a href="{link}">Ссылка на место в 2ГИС</a>'
        )

        await update.message.reply_text(reply_text, parse_mode="HTML")

        greeting = new_round(user_id, context)
        await update.message.reply_text(greeting)
        return

    user_logger.info(f"MODEL: {reply}")
    await update.message.reply_text(reply)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset_cmd))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    logging.info("Bot is running…  Ctrl‑C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()
