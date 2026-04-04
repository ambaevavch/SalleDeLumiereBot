import os
import json
import requests
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.enums import ChatMemberStatus
import asyncio

BOT_TOKEN = "8754058728:AAEc4420vw7LKJnScRKujASyt7lexQwYf8w"
ADMIN_IDS = [613610675]

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
warnings_db = {}

# ===== ХЕНДЛЕРЫ (они остаются async) =====
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
    await message.reply("🤖 Бот работает на Render!")

@dp.message(Command("ban"))
async def ban_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Нет прав!")
        return
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ Ответьте на сообщение")
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

# ===== ВЕБ-ЭНДПОИНТЫ (синхронные, без async) =====
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Telegram отправляет обновления сюда (синхронная версия)"""
    try:
        update_data = request.get_json()
        update = types.Update(**update_data)
        
        # Запускаем асинхронную обработку в синхронном контексте
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(dp.feed_update(bot, update))
        loop.close()
        
        return jsonify({"ok": True}), 200
    except Exception as e:
        print(f"Error in webhook: {e}")
        return jsonify({"ok": False}), 500

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return "OK", 200

@app.route('/')
def index():
    return "Bot is running!", 200

# ===== УСТАНОВКА WEBHOOK =====
def setup_webhook():
    """Устанавливает webhook при старте"""
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')
    webhook_url = f"https://{hostname}/webhook/{BOT_TOKEN}"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"
    try:
        response = requests.get(url)
        print(f"Webhook setup response: {response.json()}")
    except Exception as e:
        print(f"Webhook setup error: {e}")

# Устанавливаем webhook при запуске
setup_webhook()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
