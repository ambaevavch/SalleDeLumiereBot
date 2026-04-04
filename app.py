import asyncio
import os
from threading import Thread
from datetime import datetime, timedelta
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.enums import ChatMemberStatus

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = "8754058728:AAEc4420vw7LKJnScRKujASyt7lexQwYf8w"
ADMIN_IDS = [613610675]  # Ваш Telegram ID
# ========================

# Flask приложение для healthcheck (чтобы бот не засыпал)
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/healthcheck')
def healthcheck():
    return "OK", 200

# Telegram бот
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
warnings_db = {}  # Хранилище для предупреждений

# ===== ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА =====
async def is_admin(message: types.Message) -> bool:
    # В личке команды доступны только если ID в списке ADMIN_IDS
    if message.chat.type == "private":
        return message.from_user.id in ADMIN_IDS
    
    # В группе проверяем, является ли пользователь администратором
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR] or message.from_user.id in ADMIN_IDS
    except:
        return False

# ===== КОМАНДА /start =====
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.reply(
        "🤖 **Бот администратор работает!**\n\n"
        "**Команды (только для админов):**\n"
        "• `/ban` - забанить пользователя\n"
        "• `/kick` - выгнать пользователя\n"
        "• `/mute 10m` - замутить на время (10m, 1h, 2d)\n"
        "• `/unmute` - размутить пользователя\n"
        "• `/warn` - выдать предупреждение (3 = кик)\n\n"
        "**Как использовать:**\n"
        "Ответьте на сообщение пользователя и напишите команду",
        parse_mode="Markdown"
    )

# ===== КОМАНДА /ban (БАН) =====
@dp.message(Command("ban"))
async def ban_cmd(message: types.Message):
    # Проверка прав
    if not await is_admin(message):
        await message.reply("❌ У вас нет прав администратора!")
        return
    
    # Проверка, что команда вызвана ответом на сообщение
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ **Ошибка!** Ответьте на сообщение пользователя командой `/ban`", parse_mode="Markdown")
        return
    
    # Защита от бана администраторов
    try:
        target_member = await bot.get_chat_member(message.chat.id, reply.from_user.id)
        if target_member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
            await message.reply("❌ Нельзя забанить администратора!")
            return
    except:
        pass
    
    try:
        await bot.ban_chat_member(message.chat.id, reply.from_user.id)
        await message.reply(f"✅ **{reply.from_user.full_name}** забанен!", parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ===== КОМАНДА /kick (ВЫГНАТЬ) =====
@dp.message(Command("kick"))
async def kick_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ У вас нет прав администратора!")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ **Ошибка!** Ответьте на сообщение пользователя командой `/kick`", parse_mode="Markdown")
        return
    
    # Защита от кика администраторов
    try:
        target_member = await bot.get_chat_member(message.chat.id, reply.from_user.id)
        if target_member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
            await message.reply("❌ Нельзя выгнать администратора!")
            return
    except:
        pass
    
    try:
        await bot.ban_chat_member(message.chat.id, reply.from_user.id)
        await bot.unban_chat_member(message.chat.id, reply.from_user.id)
        await message.reply(f"👢 **{reply.from_user.full_name}** исключён из чата!", parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ===== КОМАНДА /mute (ЗАМУТИТЬ) =====
@dp.message(Command("mute"))
async def mute_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ У вас нет прав администратора!")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ **Ошибка!** Ответьте на сообщение пользователя командой `/mute 10m`\nДоступно: 10m, 1h, 2d", parse_mode="Markdown")
        return
    
    # Защита от мута администраторов
    try:
        target_member = await bot.get_chat_member(message.chat.id, reply.from_user.id)
        if target_member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
            await message.reply("❌ Нельзя замутить администратора!")
            return
    except:
        pass
    
    # Парсим время
    args = message.text.split()
    duration_str = args[1] if len(args) > 1 else "10m"
    
    duration_map = {"m": 1, "h": 60, "d": 1440}
    unit = duration_str[-1]
    if unit not in duration_map:
        await message.reply("❌ Неверный формат! Используйте: 10m, 1h, 2d")
        return
    
    try:
        value = int(duration_str[:-1])
        mute_minutes = value * duration_map[unit]
        until_date = datetime.now() + timedelta(minutes=mute_minutes)
        
        permissions = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(message.chat.id, reply.from_user.id, permissions, until_date=until_date)
        
        # Текст с информацией о муте
        time_text = f"{value}{'м' if unit == 'm' else 'ч' if unit == 'h' else 'д'}"
        await message.reply(f"🔇 **{reply.from_user.full_name}** замьючен на {time_text}!", parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ===== КОМАНДА /unmute (РАЗМУТИТЬ) =====
@dp.message(Command("unmute"))
async def unmute_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ У вас нет прав администратора!")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ **Ошибка!** Ответьте на сообщение пользователя командой `/unmute`", parse_mode="Markdown")
        return
    
    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        await bot.restrict_chat_member(message.chat.id, reply.from_user.id, permissions)
        await message.reply(f"🔊 **{reply.from_user.full_name}** размьючен!", parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ===== КОМАНДА /warn (ПРЕДУПРЕЖДЕНИЕ) =====
@dp.message(Command("warn"))
async def warn_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ У вас нет прав администратора!")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ **Ошибка!** Ответьте на сообщение пользователя командой `/warn`", parse_mode="Markdown")
        return
    
    # Защита от варна администраторов
    try:
        target_member = await bot.get_chat_member(message.chat.id, reply.from_user.id)
        if target_member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
            await message.reply("❌ Нельзя выдать предупреждение администратору!")
            return
    except:
        pass
    
    user_id = reply.from_user.id
    chat_id = message.chat.id
    user_name = reply.from_user.full_name
    
    # Инициализация счётчика для чата
    if chat_id not in warnings_db:
        warnings_db[chat_id] = {}
    if user_id not in warnings_db[chat_id]:
        warnings_db[chat_id][user_id] = 0
    
    # Добавляем предупреждение
    warnings_db[chat_id][user_id] += 1
    current_warns = warnings_db[chat_id][user_id]
    
    if current_warns >= 3:
        # 3 предупреждения -> кик
        try:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
            await message.reply(f"⚠️ **{user_name}** получил 3 предупреждения и был исключён из чата!", parse_mode="Markdown")
            # Сбрасываем счётчик
            del warnings_db[chat_id][user_id]
        except Exception as e:
            await message.reply(f"❌ Ошибка при исключении: {e}")
    else:
        await message.reply(f"⚠️ **{user_name}** получил предупреждение {current_warns}/3", parse_mode="Markdown")

# ===== КОМАНДА /info (информация о пользователе) =====
@dp.message(Command("info"))
async def info_cmd(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ У вас нет прав администратора!")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply("⚠️ **Ошибка!** Ответьте на сообщение пользователя командой `/info`", parse_mode="Markdown")
        return
    
    user = reply.from_user
    try:
        member = await bot.get_chat_member(message.chat.id, user.id)
        status_map = {
            ChatMemberStatus.CREATOR: "👑 Создатель",
            ChatMemberStatus.ADMINISTRATOR: "🛡️ Администратор",
            ChatMemberStatus.MEMBER: "👤 Участник",
            ChatMemberStatus.RESTRICTED: "🔇 Ограничен",
            ChatMemberStatus.BANNED: "🚫 Забанен"
        }
        status_text = status_map.get(member.status, "❓ Неизвестно")
        
        # Получаем количество предупреждений
        warns = warnings_db.get(message.chat.id, {}).get(user.id, 0)
        
        info_text = (
            f"📋 **Информация о пользователе:**\n\n"
            f"• **Имя:** {user.full_name}\n"
            f"• **ID:** `{user.id}`\n"
            f"• **Статус:** {status_text}\n"
            f"• **Предупреждения:** {warns}/3"
        )
        await message.reply(info_text, parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ===== ЗАПУСК БОТА =====
async def run_bot():
    print("🚀 Бот запущен!")
    print(f"✅ Бот: @{(await bot.get_me()).username}")
    print(f"👥 Администраторы: {ADMIN_IDS}")
    print("\n📋 Доступные команды:")
    print("   /ban - забанить")
    print("   /kick - выгнать")
    print("   /mute - замутить")
    print("   /unmute - размутить")
    print("   /warn - предупреждение")
    print("   /info - информация о пользователе")
    await dp.start_polling(bot)

def start_bot_thread():
    asyncio.run(run_bot())

# ===== ТОЧКА ВХОДА =====
if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=start_bot_thread, daemon=True)
    bot_thread.start()
    # Запускаем Flask для healthcheck
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)
