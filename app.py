import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.enums import ChatMemberStatus
from datetime import datetime, timedelta

BOT_TOKEN = "8754058728:AAEc4420vw7LKJnScRKujASyt7lexQwYf8w"
ADMIN_IDS = [613610675]

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
    await message.reply("🤖 Бот администратор работает!\n\nКоманды:\n/ban - забанить\n/kick - выгнать\n/mute - замутить\n/unmute - размутить\n/warn - предупредить")

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

async def main():
    print("🚀 Бот запущен!")
    print(f"✅ Бот: @{(await bot.get_me()).username}")
    print(f"👥 Администраторы: {ADMIN_IDS}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
