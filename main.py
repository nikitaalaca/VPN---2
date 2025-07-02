import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties

from db import (
    get_subscription, set_subscription, has_used_trial,
    deactivate_expired_users, get_all_users,
    is_admin, is_moderator, add_admin, remove_admin,
    delete_user, update_v2ray_key, get_v2ray_key
)

from keep_alive import keep_alive  # Защита от сна Replit

import os
API_TOKEN = os.getenv("API_TOKEN")
import os
ADMIN_ID = os.getenv("MAIN_ADMIN_ID")

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Клавиатура обычного пользователя
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📄 Профиль"), KeyboardButton(text="💳 Купить подписку")],
        [KeyboardButton(text="📥 Инструкция"), KeyboardButton(text="📞 Связь с админом")]
    ],
    resize_keyboard=True
)

tariff_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Тест на 3 дня")],
        [KeyboardButton(text="🔓 30 дней"), KeyboardButton(text="🔐 90 дней")],
        [KeyboardButton(text="🔁 Назад в меню")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="🧾 Выдать подписку")],
        [KeyboardButton(text="🗑 Удалить пользователя"), KeyboardButton(text="🔁 Рестарт бота")],
        [KeyboardButton(text="➕ Админ"), KeyboardButton(text="➖ Удалить админа")],
        [KeyboardButton(text="🔑 Обновить ключ"), KeyboardButton(text="📊 Показать ключ")],
        [KeyboardButton(text="🔁 Назад в меню")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def handle_start(message: Message):
    if message.from_user.id == MAIN_ADMIN_ID:
        await message.answer("👋 Привет, главный админ!", reply_markup=admin_menu)
    else:
        await message.answer("Привет! Я VPN бот. Выбери действие 👇", reply_markup=main_menu)

@dp.message(F.text == "📄 Профиль")
async def handle_profile(message: Message):
    user_id = str(message.from_user.id)
    now = datetime.utcnow()
    sub_until = get_subscription(user_id)
    v2ray_key = get_v2ray_key(user_id)

    if sub_until and sub_until > now:
        days = (sub_until - now).days
        await message.answer(
            f"👤 Ваш профиль:\n\n<b>Подписка активна</b>\nДо: <b>{sub_until.strftime('%d.%m.%Y %H:%M')}</b>\n"
            f"Осталось: <b>{days} дней</b>\n\n🔑 Ключ:\n<code>{v2ray_key}</code>"
        )
    else:
        await message.answer("👤 У вас <b>нет активной подписки</b>.\nНажмите «Купить подписку» чтобы активировать.")

@dp.message(F.text == "💳 Купить подписку")
async def handle_buy(message: Message):
    await message.answer("💳 Выберите тариф:", reply_markup=tariff_menu)

@dp.message(F.text == "🚀 Тест на 3 дня")
async def handle_trial(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "без username"
    now = datetime.utcnow()

    if has_used_trial(user_id):
        await message.answer("❗️Вы уже использовали тест. Повторно его получить нельзя.")
        return

    expire_time = set_subscription(user_id, username, 3, trial=True)

    key = f"vless://{user_id}@vpn.example.com:443?encryption=none&security=tls&type=grpc&serviceName=vpn#TestVPN"
    update_v2ray_key(user_id, key)

    await message.answer(
        f"✅ <b>Выдан тест на 3 дня</b> до <b>{expire_time.strftime('%d.%m.%Y %H:%M')}</b>\n\n🔑 Ключ:\n<code>{key}</code>"
    )

@dp.message(F.text.in_({"🔓 30 дней", "🔐 90 дней"}))
async def handle_paid_tariffs(message: Message):
    await message.answer("💰 Для покупки напишите админу: @your_admin")

@dp.message(F.text == "📥 Инструкция")
async def handle_instructions(message: Message):
    await message.answer(
        "📥 <b>Инструкция по подключению:</b>\n\n"
        "1. Скачайте V2Ray клиент:\nhttps://apps.apple.com/app/id6446208239\n\n"
        "2. Скопируйте ключ\n"
        "3. Вставьте в клиент\n\n"
        "🔐 Если нужна помощь — жмите 'Связь с админом'"
    )

@dp.message(F.text == "📞 Связь с админом")
async def handle_support(message: Message):
    await message.answer("📞 Напишите администратору: @your_admin")

@dp.message(F.text == "🔁 Назад в меню")
async def handle_back(message: Message):
    if message.from_user.id == MAIN_ADMIN_ID:
        await message.answer("↩️ Главное админ-меню", reply_markup=admin_menu)
    else:
        await message.answer("↩️ Главное меню", reply_markup=main_menu)

# 🔧 Админ-функции

@dp.message(F.text == "👥 Пользователи")
async def show_users(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    users = get_all_users()
    await message.answer(f"👥 Всего пользователей: <b>{len(users)}</b>")

@dp.message(F.text == "🧾 Выдать подписку")
async def give_sub(message: Message):
    await message.answer("✍️ Напишите в формате:\n<code>/sub ID_пользователя дней</code>")

@dp.message(Command("sub"))
async def cmd_sub(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    try:
        _, uid, days = message.text.split()
        expire_time = set_subscription(uid, "admin_set", int(days), trial=False)
        await message.answer(f"✅ Подписка до: <b>{expire_time.strftime('%d.%m.%Y %H:%M')}</b>")
    except:
        await message.answer("❌ Ошибка. Пример: /sub 123456789 30")

@dp.message(F.text == "🔑 Обновить ключ")
async def update_key(message: Message):
    user_id = str(message.from_user.id)
    new_key = f"vless://{user_id}@vpn.example.com:443?security=tls#Updated"
    update_v2ray_key(user_id, new_key)
    await message.answer(f"🔑 Ключ обновлён:\n<code>{new_key}</code>")

@dp.message(F.text == "📊 Показать ключ")
async def show_key(message: Message):
    user_id = str(message.from_user.id)
    key = get_v2ray_key(user_id)
    if key:
        await message.answer(f"🔑 Ваш ключ:\n<code>{key}</code>")
    else:
        await message.answer("❌ Ключ не найден.")

@dp.message(F.text == "🗑 Удалить пользователя")
async def delete_command(message: Message):
    await message.answer("✍️ Напишите:\n<code>/del ID</code>")

@dp.message(Command("del"))
async def delete_user_cmd(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    try:
        _, uid = message.text.split()
        delete_user(uid)
        await message.answer(f"✅ Пользователь {uid} удалён.")
    except:
        await message.answer("❌ Ошибка. Пример: /del 123456789")

@dp.message(F.text == "🔁 Рестарт бота")
async def restart_bot(message: Message):
    await message.answer("🔄 Бот перезапускается...")
    os.execl(sys.executable, sys.executable, *sys.argv)

@dp.message(F.text == "➕ Админ")
async def add_admin_cmd(message: Message):
    await message.answer("Напиши /addadmin ID")

@dp.message(Command("addadmin"))
async def handle_add_admin(message: Message):
    _, uid = message.text.split()
    add_admin(uid)
    await message.answer(f"✅ Назначен админ: {uid}")

@dp.message(F.text == "➖ Удалить админа")
async def del_admin_cmd(message: Message):
    await message.answer("Напиши /deladmin ID")

@dp.message(Command("deladmin"))
async def handle_del_admin(message: Message):
    _, uid = message.text.split()
    remove_admin(uid)
    await message.answer(f"✅ Удалён админ: {uid}")

# 🔁 Главный запуск

async def main():
    keep_alive()  # Защита от сна на Replit
    deactivate_expired_users()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
