import asyncio
import os
import sys
import signal
import logging
import traceback

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Игнорируем сигналы
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGTERM, signal.SIG_IGN)

import os
import asyncio
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.enums import ChatMemberStatus
from datetime import datetime, timedelta
import requests

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = "8754058728:AAEc4420vw7LKJnScRKujASyt7lexQwYf8w"
ADMIN_IDS = [613610675]
# ========================

flask_app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
warnings_db = {}

# ===== ХЕНДЛЕРЫ КОМАНД =====
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
    logger.info(f"Получена команда /start от {message.from_user.id}")
    await message.reply(
        "🤖 **Бот администратор работает!**\n\n"
        "**Команды:**\n"
        "• `/ban` - забанить\n"
        "• `/kick` - выгнать\n"
        "• `/mute 10m` - замутить\n"
        "• `/unmute` - размутить\n"
        "• `/warn` - предупредить\n\n"
        "**Как использовать:** Ответьте на сообщение и напишите команду",
        parse_mode="Markdown"
    )

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
    args = message.text.split()
    duration_str = args[1] if len(args) > 1 else "10m"
    duration_map = {"m": 1, "h": 60, "d": 1440}
    unit = duration_str[-1]
    if unit not in duration_map:
        await message.reply("❌ Используйте: 10m, 1h, 2d")
        return
    try:
        value = int(duration_str[:-1])
        until_date = datetime.now() + timedelta(minutes=value * duration_map[unit])
        permissions = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(message.chat.id, reply.from_user.id, permissions, until_date=until_date)
        await message.reply(f"🔇 {reply.from_user.full_name} замьючен на {duration_str}")
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
        await message.reply(f"⚠️ {reply.from_user.full_name} исключён (3 предупреждения)")
        del warnings_db[cid][uid]
    else:
        await message.reply(f"⚠️ {reply.from_user.full_name} предупреждение {current}/3")

@dp.message(Command("info"))
async def info_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Нет прав!")
        return
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ Ответьте на сообщение")
        return
    user = reply.from_user
    warns = warnings_db.get(message.chat.id, {}).get(user.id, 0)
    await message.reply(f"📋 **{user.full_name}**\nID: `{user.id}`\nПредупреждения: {warns}/3", parse_mode="Markdown")

# ===== WEBHOOK ENDPOINT =====
@flask_app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Telegram отправляет обновления сюда"""
    logger.info("=== Webhook получил запрос ===")
    logger.info(f"Headers: {dict(request.headers)}")
    
    try:
        update_data = request.get_json()
        logger.info(f"Update data: {update_data}")
        
        update = types.Update(**update_data)
        logger.info(f"Update создан: {update.update_id}")
        
        # Создаём новый event loop для обработки
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("Event loop создан")
        
        loop.run_until_complete(dp.feed_update(bot, update))
        logger.info("Update успешно обработан")
        loop.close()
        
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"!!! ОШИБКА В WEBHOOK: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"ok": False, "error": str(e)}), 500

@flask_app.route('/healthcheck')
def healthcheck():
    return "OK", 200

@flask_app.route('/')
def index():
    return "Bot is running!", 200

# ===== УСТАНОВКА WEBHOOK =====
def setup_webhook():
    """Устанавливает webhook при запуске"""
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')
    webhook_url = f"https://{hostname}/webhook/{BOT_TOKEN}"
    
    logger.info(f"Настройка webhook на URL: {webhook_url}")
    
    # Удаляем старый webhook
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    
    # Устанавливаем новый
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"
    try:
        response = requests.get(url)
        logger.info(f"Webhook setup response: {response.json()}")
    except Exception as e:
        logger.error(f"Webhook setup error: {e}")

# Устанавливаем webhook при запуске
setup_webhook()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Запуск Flask на порту {port}")
    flask_app.run(host='0.0.0.0', port=port)
