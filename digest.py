from aiogram import Bot
from datetime import datetime, timedelta
import database as db
import ai_service
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def collect_messages(bot: Bot, chat_id: int, limit_per_topic: int = 50):
    messages = []
    now = datetime.now()
    yesterday = now - timedelta(hours=24)
    
    logger.info(f"[{chat_id}] Начало сбора сообщений...")
    
    try:
        topics = await bot.get_forum_topics(chat_id=chat_id)
        logger.info(f"[{chat_id}] Найдено топиков: {len(topics)}")
        
        for topic in topics:
            topic_id = topic.message_thread_id
            
            try:
                history = await bot.get_chat_history(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    limit=limit_per_topic
                )
                
                for msg in history:
                    if msg.date < yesterday:
                        continue
                    if msg.from_user and msg.from_user.is_bot:
                        continue
                    if msg.service:
                        continue
                        
                    user_name = msg.from_user.username or msg.from_user.first_name or "Аноним"
                    
                    custom_nick = await db.get_user_nickname(chat_id, msg.from_user.id)
                    if custom_nick:
                        user_name = custom_nick
                    
                    text = msg.text or msg.caption or ""
                    image_desc = None
                    
                    if msg.photo:
                        file = await bot.get_file(msg.photo[-1].file_id)
                        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
                        image_desc = await ai_service.describe_image(file_url)
                        if not text:
                            text = "[Отправил фото]"
                    
                    messages.append({
                        'user': user_name,
                        'text': text,
                        'id': msg.message_id,
                        'topic_id': topic_id,
                        'image_desc': image_desc,
                        'date': msg.date
                    })
                    
                    await db.mark_message_processed(
                        chat_id, msg.message_id, topic_id, int(msg.date.timestamp())
                    )
            except Exception as e:
                logger.error(f"[{chat_id}] Ошибка чтения топика {topic_id}: {e}")
    
    except Exception as e:
        logger.error(f"[{chat_id}] Ошибка получения списка топиков: {e}")
    
    messages.sort(key=lambda x: x['date'], reverse=True)
    logger.info(f"[{chat_id}] Всего собрано сообщений: {len(messages)}")
    return messages[:100]

async def send_daily_digest(bot: Bot, chat_id: int, topic_id: int, style: str):
    logger.info(f"[{datetime.now()}] Запуск сборки дайджеста для чата {chat_id}...")
    
    messages = await collect_messages(bot, chat_id)
    
    # ИЗМЕНЕНО: Минимум 1 сообщение вместо 5 (для теста)
    if len(messages) < 1:
        logger.warning(f"[{chat_id}] Слишком мало сообщений ({len(messages)}) для дайджеста")
        return
    
    logger.info(f"[{chat_id}] Генерация текста (стиль: {style})...")
    digest_text = await ai_service.generate_digest_text(
        messages, 
        style, 
        chat_id,
        config.SPONSOR_TEXT,
        config.SPONSOR_LINK
    )
    
    if not digest_text or digest_text.startswith("❌"):
        logger.error(f"[{chat_id}] Ошибка генерации текста: {digest_text}")
        return
    
    logger.info(f"[{chat_id}] Отправка в топик {topic_id}...")
    
    try:
        if len(digest_text) > 4000:
            parts = [digest_text[i:i+4000] for i in range(0, len(digest_text), 4000)]
            for part in parts:
                await bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    text=part,
                    parse_mode="HTML"
                )
        else:
            await bot.send_message(
                chat_id=chat_id,
                message_thread_id=topic_id,
                text=digest_text,
                parse_mode="HTML"
            )
        logger.info(f"[{chat_id}] Дайджест успешно отправлен!")
    except Exception as e:
        logger.error(f"[{chat_id}] Ошибка отправки: {e}")
