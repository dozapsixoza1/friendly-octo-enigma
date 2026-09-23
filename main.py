import asyncio
import json
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    LabeledPrice,
    PreCheckoutQuery,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

BOT_TOKEN = "8650738832:AAEd6RIeS-lDFJH99t3KkjE_jymKiIS7aQE"
WEBAPP_URL = "https://otdelapp.vercel.app/"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

SHOP = {
    "prefix": ("Префикс в чате", 50),
    "title": ("Название чата", 80),
    "desc": ("Описание чата", 60),
    "photo": ("Фото чата", 70),
    "tag": ("Тэг в чате", 100),
    "freezebuy": ("Заморозка чата", 150),
    "banbuy": ("Бан пользователя", 120),
    "mutebuy": ("Мут пользователя", 90),
}


def main_kb() -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(
            text="🎛 Открыть панель",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )
    ]]
    rows.append([InlineKeyboardButton(text="⭐ Тестовый счёт (10 Stars)", callback_data="test_invoice")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(CommandStart())
async def on_start(message: Message):
    text = (
        f"Привет, {message.from_user.first_name}!\n\n"
        "Я управляю этим чатом: события, модерация и магазин прямо из мини-приложения.\n"
        "Добавь меня в чат как админа и открывай панель ниже."
    )
    await message.answer(text, reply_markup=main_kb())


@dp.callback_query(F.data == "test_invoice")
async def test_invoice(callback):
    await send_stars_invoice(callback.message.chat.id, "test", "Тестовый платёж", 10)
    await callback.answer()


async def send_stars_invoice(chat_id: int, payload_id: str, title: str, stars: int):
    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=f"Оплата: {title}",
        payload=payload_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars)],
    )


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)


@dp.message(F.successful_payment)
async def on_paid(message: Message):
    payload = message.successful_payment.invoice_payload
    stars = message.successful_payment.total_amount
    if payload in SHOP:
        name = SHOP[payload][0]
        await message.answer(f"Оплачено ⭐ {stars} — «{name}» применено к чату.")
    else:
        await message.answer(f"Оплата на ⭐ {stars} прошла успешно.")


@dp.message(F.web_app_data)
async def on_webapp_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("Не смог разобрать данные из панели.")
        return

    action = data.get("action")

    if action == "buy":
        item_id = data.get("item")
        if item_id not in SHOP:
            await message.answer("Такого товара нет.")
            return
        name, price = SHOP[item_id]
        await send_stars_invoice(message.chat.id, item_id, name, price)
        return

    handlers = {
        "event_777": "Запускаю ивент 777 🎰",
        "event_spam3": "Запускаю ивент «Перебив сообщений» ⚡",
        "event_guess": "Запускаю ивент «Угадай цифры» 🔢",
        "mute": "Мут выполнен",
        "unmute": "Размут выполнен",
        "ban": "Бан выполнен",
        "unban": "Разбан выполнен",
        "warn": "Варн выдан",
        "unwarn": "Варн снят",
        "freeze": "Чат заморожен",
        "unfreeze": "Чат разморожен",
    }
    await message.answer(handlers.get(action, f"Получено действие: {action}"))


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Webhook сброшен, запускаю polling")
    try:
        await dp.start_polling(bot)
    except Exception:
        logging.exception("Polling упал с ошибкой")
        raise


if __name__ == "__main__":
    asyncio.run(main())
