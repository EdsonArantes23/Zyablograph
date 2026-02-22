import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import config
import database as db
import digest
import ai_service

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

async def is_admin_private(message: Message) -> bool:
    if message.chat.type != 'private':
        await message.answer("❌ Эта команда работает только в личных сообщениях с ботом!")
        return False
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде!")
        logging.warning(f"Попытка доступа от пользователя {message.from_user.id}")
        return False
    return True

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await db.init_db()
    if message.chat.type != 'private':
        return
    if message.from_user.id != config.ADMIN_ID:
        return
    
    chats = await db.get_all_chats()
    chats_list = "\n".join([f"• {c[1]} ({c[0]})" for c in chats]) if chats else "Нет настроенных чатов"
    
    text = f"""
🎉 <b>Бот для дайджестов чатов готов!</b>

📋 <b>Настроенные чаты:</b>
{chats_list}

📝 <b>Команды (только в ЛС для админа):</b>
• /addchat [ID] [топик] - добавить чат для анализа
• /removechat [ID] - удалить чат
• /list - показать все чаты
• /style [ID] [стиль] - установить стиль
• /topic [ID] [топик] - установить топик для отправки
• /enable [ID] - включить чат
• /disable [ID] - выключить чат
• /settime [ID] [HH:MM] - время дайджеста
• /nickname [текст] - установить ник (ОТВЕТОМ на сообщение в группе)
• /test [ID] - тестовый дайджест
• /status - статус бота

🗣 <b>Команды для всех (в чате):</b>
• /ask [вопрос] - задать вопрос боту (саркастический ответ)
• @Зяблограф [вопрос] - упомянуть бота для ответа

⏰ Время по умолчанию: {config.DIGEST_HOUR}:{config.DIGEST_MINUTE} UTC
"""
    await message.answer(text)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    if not await is_admin_private(message):
        return
    
    text = """
📚 <b>Справка по командам:</b>

<b>📋 Управление чатами (ТОЛЬКО АДМИН В ЛС):</b>
• /addchat [ID] [топик] - добавить чат
• /removechat [ID] - удалить чат
• /list - показать все чаты
• /enable [ID] - включить чат
• /disable [ID] - выключить чат

<b>⚙️ Настройки (ТОЛЬКО АДМИН В ЛС):</b>
• /style [ID] [стиль] - hardcore, classic, neutral, love, custom
• /topic [ID] [топик] - топик для отправки дайджеста
• /settime [ID] [HH:MM] - время дайджеста (UTC)

<b>👤 Пользователи (ТОЛЬКО АДМИН В ЛС):</b>
• /nickname [текст] - установить ник пользователю
  (Ответьте на сообщение в группе, затем напишите в ЛС боту)

<b>🗣 Вопросы (ВСЕ В ЧАТЕ + АДМИН В ЛС):</b>
• /ask [вопрос] - задать вопрос боту (саркастический ответ)
• @Зяблограф [вопрос] - упомянуть бота для ответа

<b>🧪 Тестирование (ТОЛЬКО АДМИН В ЛС):</b>
• /test [ID] - тестовый дайджест
• /status - статус бота

⚠️ Команды настройки работают ТОЛЬКО в личных сообщениях!
🔒 Доступ к настройкам только для админа (ID: 417850992)
ℹ️ Команда /ask доступна всем в чате!
"""
    await message.answer(text)

@dp.message(Command("addchat"))
async def cmd_addchat(message: Message):
    if not await is_admin_private(message):
        return
    
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("❌ Использование: /addchat [ID_чата] [ID_топика]\nПример: /addchat -1001234567890 1")
    
    chat_id = int(args[1])
    topic_id = int(args[2]) if len(args) > 2 else 1
    
    try:
        chat_info = await bot.get_chat(chat_id)
        await db.add_chat(chat_id, chat_info.title, topic_id)
        await message.answer(f"✅ Чат <b>{chat_info.title}</b> добавлен!\n📥 Читать: ВСЕ ветки\n📤 Писать: Ветка {topic_id}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\nПроверьте что бот добавлен в чат как админ")

@dp.message(Command("removechat"))
async def cmd_removechat(message: Message):
    if not await is_admin_private(message):
        return
    
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("❌ Использование: /removechat [ID_чата]")
    
    chat_id = int(args[1])
    await db.remove_chat(chat_id)
    await message.answer(f"✅ Чат {chat_id} удалён из настроек")

@dp.message(Command("list"))
async def cmd_list(message: Message):
    if not await is_admin_private(message):
        return
    
    chats = await db.get_all_chats()
    if not chats:
        return await message.answer("📋 Нет настроенных чатов")
    
    text = "📋 <b>Настроенные чаты:</b>\n\n"
    for c in chats:
        chat_id, title, style, topic_id, enabled, hour, minute = c
        status = "🟢" if enabled else "🔴"
        text += f"{status} <b>{title}</b>\n"
        text += f"   ID: {chat_id} | 📤 Топик отчета: {topic_id}\n"
        text += f"   Стиль: {style} | Время: {hour}:{minute}\n\n"
    
    await message.answer(text)

@dp.message(Command("style"))
async def cmd_style(message: Message):
    if not await is_admin_private(message):
        return
    
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("❌ Использование: /style [ID_чата] [стиль]\nСтили: hardcore, classic, neutral, love, custom")
    
    chat_id = int(args[1])
    style = args[2]
    
    if style not in ai_service.STYLES:
        return await message.answer(f"❌ Доступные стили: {', '.join(ai_service.STYLES.keys())}")
    
    await db.update_chat_style(chat_id, style)
    await message.answer(f"✅ Стиль для чата {chat_id} установлен: <b>{style}</b>")

@dp.message(Command("topic"))
async def cmd_topic(message: Message):
    if not await is_admin_private(message):
        return
    
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("❌ Использование: /topic [ID_чата] [ID_топика]\n⚠️ Меняет только КУДА отправлять отчет!")
    
    chat_id = int(args[1])
    topic_id = int(args[2])
    
    await db.update_chat_topic(chat_id, topic_id)
    await message.answer(f"✅ Топик для ОТПРАВКИ в чате {chat_id} установлен: <b>{topic_id}</b>")

@dp.message(Command("enable"))
async def cmd_enable(message: Message):
    if not await is_admin_private(message):
        return
    
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("❌ Использование: /enable [ID_чата]")
    
    chat_id = int(args[1])
    await db.toggle_chat_enabled(chat_id, 1)
    await message.answer(f"✅ Чат {chat_id} включён")

@dp.message(Command("disable"))
async def cmd_disable(message: Message):
    if not await is_admin_private(message):
        return
    
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("❌ Использование: /disable [ID_чата]")
    
    chat_id = int(args[1])
    await db.toggle_chat_enabled(chat_id, 0)
    await message.answer(f"🔴 Чат {chat_id} выключен")

@dp.message(Command("settime"))
async def cmd_settime(message: Message):
    if not await is_admin_private(message):
        return
    
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("❌ Использование: /settime [ID_чата] [HH:MM]")
    
    chat_id = int(args[1])
    time_str = args[2]
    
    try:
        hour, minute = map(int, time_str.split(':'))
        await db.update_chat_time(chat_id, hour, minute)
        await message.answer(f"✅ Время для чата {chat_id} установлено: <b>{hour}:{minute} UTC</b>")
    except:
        await message.answer("❌ Неверный формат времени. Пример: 20:00")

@dp.message(Command("nickname"))
async def cmd_nickname(message: Message):
    if not await is_admin_private(message):
        return
    
    if not message.reply_to_message:
        return await message.answer(
            "❌ <b>Как установить никнейм:</b>\n\n"
            "1️⃣ Ответьте на сообщение пользователя в группе\n"
            "2️⃣ Напишите в ЛС боту: /nickname [новый ник]\n\n"
            "Пример: /nickname Васян Пупкин"
        )
    
    nickname = message.text.replace("/nickname", "").strip()
    if not nickname:
        return await message.answer("❌ Укажите никнейм после команды")
    
    target = message.reply_to_message.from_user
    chat_id = message.reply_to_message.chat.id
    
    await db.set_user_nickname(chat_id, target.id, nickname)
    await message.answer(f"✅ <b>{target.first_name}</b> теперь <b>{nickname}</b>\n(в чате {chat_id})")

@dp.message(Command("test"))
async def cmd_test(message: Message):
    if not await is_admin_private(message):
        return
    
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("❌ Использование: /test [ID_чата]")
    
    chat_id = int(args[1])
    config_chat = await db.get_chat_config(chat_id)
    
    if not config_chat:
        return await message.answer("❌ Чат не найден в настройках. Добавьте через /addchat")
    
    await message.answer("🔄 Запускаю тестовый дайджест...\n📥 Читаю ВСЕ ветки...\n📤 Пишу в ветку {topic_id}".format(topic_id=config_chat[3]))
    logging.info(f"ADMIN {message.from_user.id} запустил тест для чата {chat_id}")
    
    try:
        await digest.send_daily_digest(bot, chat_id, config_chat[3], config_chat[2])
        await message.answer("✅ Дайджест отправлен! (Проверьте логи и чат)")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")
        logging.error(f"Ошибка теста: {e}")

@dp.message(Command("status"))
async def cmd_status(message: Message):
    if not await is_admin_private(message):
        return
    
    chats = await db.get_all_chats()
    text = f"""
📊 <b>Статус бота:</b>

✅ Бот активен
👤 Админ: {config.ADMIN_ID}
📁 Чатов настроено: {len(chats)}
⏰ Время по умолчанию: {config.DIGEST_HOUR}:{config.DIGEST_MINUTE} UTC
"""
    await message.answer(text)

@dp.message(Command("ask"))
async def cmd_ask(message: Message):
    question = message.text.replace("/ask", "").strip()
    
    if not question:
        return await message.answer("❌ Задай вопрос! Пример: /ask кто тут главный?")
    
    if message.chat.type == 'private':
        if message.from_user.id != config.ADMIN_ID:
            return await message.answer("❌ В ЛС эта команда доступна только админу!")
        chat_id = config.MAIN_CHAT_ID if hasattr(config, 'MAIN_CHAT_ID') else -1002977868330
    else:
        chat_id = message.chat.id
    
    chat_config = await db.get_chat_config(chat_id)
    if not chat_config:
        style = 'hardcore'
    else:
        style = chat_config[2]
    
    try:
        history = await bot.get_chat_history(chat_id, limit=10)
        context = "\n".join([
            f"{m.from_user.first_name if m.from_user else 'Bot'}: {m.text or ''}" 
            for m in history 
            if m.text and not m.from_user.is_bot
        ])
    except:
        context = ""
    
    await message.reply("🤔 Думаю, блять...")
    answer = await ai_service.ai_answer(question, context, style)
    await message.answer(answer)

@dp.message(F.bot_mentioned)
async def ai_mention(message: Message):
    chat_config = await db.get_chat_config(message.chat.id)
    if not chat_config or not chat_config[4]:
        return
    
    style = chat_config[2]
    question = message.text.replace(f"@{bot.username}", "").strip()
    
    if not question:
        return await message.answer("❌ Тыкнул и молчишь? Спрашивай давай!")
    
    history = await bot.get_chat_history(message.chat.id, limit=10)
    context = "\n".join([f"{m.from_user.first_name if m.from_user else 'Bot'}: {m.text or ''}" for m in history if m.text])
    
    await message.reply("🤔 Думаю, блять...")
    answer = await ai_service.ai_answer(question, context, style)
    await message.answer(answer)

async def scheduled_digest():
    chats = await db.get_all_chats()
    now = datetime.now()
    
    for chat in chats:
        chat_id, title, style, topic_id, enabled, hour, minute = chat
        if now.hour == hour and now.minute == minute:
            await digest.send_daily_digest(bot, chat_id, topic_id, style)

async def main():
    await db.init_db()
    scheduler.add_job(scheduled_digest, 'cron', minute='*')
    scheduler.start()
    print(f"🤖 Бот запущен!")
    print(f"👤 Админ ID: {config.ADMIN_ID}")
    print(f"⏰ Проверка дайджеста: каждую минуту")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
