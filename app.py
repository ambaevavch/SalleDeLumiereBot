import asyncio
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.enums import ChatMemberStatus
from flask import Flask
import threading

# ===== ВАШИ ДАННЫЕ =====
BOT_TOKEN = "8754058728:AAEc4420vw7LKJnScRKujASyt7lexQwYf8w"
ADMIN_IDS = [613610675]
# ========================

# Создаем Flask приложение для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

@app.route('/health')
def health():
    return "OK"

# Сам бот
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
warnings_db = {}

async def is_admin(message: types.Message) -> bool:
    if message.chat.type == "private":
        return message.from_user.id in ADMIN_IDS
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR] or message.from_user.id in ADMIN_IDS
    except:
        return False

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.reply("🤖 Бот администратор работает!")

@dp.message(Command("ban"))
async def ban_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Нет прав!")
        return
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ Ответьте на сообщение пользователя")
        return
    try:
        await bot.ban_chat_member(message.chat.id, reply.from_user.id)
        await message.reply(f"✅ {reply.from_user.full_name} забанен!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("kick"))
async def kick_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Нет прав!")
        return
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ Ответьте на сообщение")
        return
    try:
        await bot.ban_chat_member(message.chat.id, reply.from_user.id)
        await bot.unban_chat_member(message.chat.id, reply.from_user.id)
        await message.reply(f"👢 {reply.from_user.full_name} исключён!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("mute"))
async def mute_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Нет прав!")
        return
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ Ответьте на сообщение")
        return
    try:
        permissions = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(message.chat.id, reply.from_user.id, permissions)
        await message.reply(f"🔇 {reply.from_user.full_name} замьючен!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("unmute"))
async def unmute_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Нет прав!")
        return
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ Ответьте на сообщение")
        return
    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        await bot.restrict_chat_member(message.chat.id, reply.from_user.id, permissions)
        await message.reply(f"🔊 {reply.from_user.full_name} размьючен!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("warn"))
async def warn_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Нет прав!")
        return
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ Ответьте на сообщение")
        return
    uid, cid = reply.from_user.id, message.chat.id
    if cid not in warnings_db:
        warnings_db[cid] = {}
    warnings_db[cid][uid] = warnings_db[cid].get(uid, 0) + 1
    current = warnings_db[cid][uid]
    if current >= 3:
        await bot.ban_chat_member(cid, uid)
        await bot.unban_chat_member(cid, uid)
        await message.reply(f"⚠️ {reply.from_user.full_name} исключён (3 варна)")
        del warnings_db[cid][uid]
    else:
        await message.reply(f"⚠️ {reply.from_user.full_name} варн {current}/3")

# Функция запуска бота в отдельном потоке
def run_bot():
    asyncio.run(main())

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

# Запускаем бота в фоновом потоке при старте Flask
if __name__ != "__main__":
    # Для Render - запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

if __name__ == "__main__":
    # Локальный запуск
    from threading import Thread
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)