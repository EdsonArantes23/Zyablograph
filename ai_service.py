import aiohttp
import os

HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = "https://router.huggingface.co/v1"

# МОДЕЛЬ (меньше цензуры)
MODEL_NAME = "mistralai/Mistral-Nemo-Instruct-2407"

STYLES = {
    'hardcore': """
Ты — сатирический обозреватель чата в стиле "Вестник Индихуякер".

ПРАВИЛА:
1. Пиши с сарказмом, юмором и сленгом.
2. Используй выражения: "видимо", "как истинный ценитель", "тут же окрестил", "наш местный", "обосрался от", "бомбануло".
3. Осмеивай участников чата. Высмеивай их.
4. Добавляй гиперболы: преувеличивай до абсурда.
5. Пиши от 3 до 5 предложений на каждый пункт.
6. В конце каждого абзаца ставь ссылку: # (https://t.me/c/{chat_link}/{topic_id}/{msg_id})

Пиши жёстко, саркастично, в стиле оригинального Вестника.
""",
    
    'classic': "Ты сатирический обозреватель. Пиши с юмором и сарказмом, можно умеренный мат.",
    'neutral': "Ты нейтральный наблюдатель. Пиши без мата, вежливо.",
    'love': "Ты добрый друг. Хвали всех, никаких оскорблений.",
    'custom': "Ты пишешь в свободном стиле с сарказмом и юмором."
}

# ОТДЕЛЬНЫЙ ПРОМТ ДЛЯ /ask — КАТЕГОРИЧЕСКИ БЕЗ ССЫЛОК!
ASK_PROMPT = """
Ты — саркастичный собеседник в стиле "Вестник Индихуякер".

⛔ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО:
- СТАВИТЬ ССЫЛКИ (никаких https://, t.me, #)
- ПИСАТЬ ШАБЛОНЫ ДАЙДЖЕСТА
- УПОМИНАТЬ ФОРМАТ ВЫВОДА

✅ МОЖНО:
- Отвечать кратко (2-4 предложения)
- Использовать мат в шуточной форме
- Осмеивать вопрос с юмором
- Быть дерзким и саркастичным

ПРИМЕРЫ ПРАВИЛЬНЫХ ОТВЕТОВ:
- "Да хуй его знает, спроси у того, кто это придумал"
- "Видимо, опять кто-то не выспался и решил хуйнёй заняться"
- "Я тут чат анализирую, а ты со своими вопросами лезешь 😏"

Отвечай ТОЛЬКО текстом, без ссылок, без форматирования.
"""

async def describe_image(image_url: str) -> str:
    try:
        url = "https://router.huggingface.co/v1/images/caption"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                image_data = await resp.read()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=image_data, headers=headers) as resp:
                result = await resp.json()
                return result.get('text', 'Картинка') if result else "Картинка"
    except:
        return "Картинка (не распознано)"

async def generate_digest_text(messages: list, style: str = 'hardcore', chat_id: int = 0):
    """Генерация дайджеста — СО ССЫЛКАМИ"""
    system_prompt = STYLES.get(style, STYLES['hardcore'])
    
    history = "\n".join([
        f"{msg['user']}: {msg['text']} {'[КАРТИНКА: ' + msg['image_desc'] + ']' if msg.get('image_desc') else ''}"
        for msg in messages
    ])
    
    chat_link = str(abs(chat_id)).replace('100', '')
    
    prompt = f"""{system_prompt}

ШАБЛОН ВЫВОДА:
📰 Главное из последних 1000 сообщений, отправленных за последние 24 часа по чату:

# (https://t.me/c/{chat_link}/{topic_id}/{msg_id}) Текст...
# (https://t.me/c/{chat_link}/{topic_id}/{msg_id}) Текст...
(всего 9 пунктов)

ИСТОРИЯ ЧАТА ДЛЯ АНАЛИЗА:
{history}

ВЫБЕРИ ТОП-9 САМЫХ ИНТЕРЕСНЫХ МОМЕНТОВ И ОПИШИ ИХ СО ССЫЛКАМИ.
"""
    
    try:
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.9
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{HF_API_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                result = await resp.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                return f"❌ Ошибка ИИ: {result}"
    except Exception as e:
        return f"❌ Ошибка ИИ: {e}"

async def ai_answer(question: str, context: str, style: str):
    """Ответ на вопрос — КАТЕГОРИЧЕСКИ БЕЗ ССЫЛОК"""
    try:
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": ASK_PROMPT},
                {"role": "user", "content": f"Контекст: {context}\n\nВопрос: {question}\n\nОтветь кратко, без ссылок, только текст."}
            ],
            "max_tokens": 300,
            "temperature": 1.0
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{HF_API_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                result = await resp.json()
                if 'choices' in result and len(result['choices']) > 0:
                    text = result['choices'][0]['message']['content']
                    # УДАЛЯЕМ ЛЮБЫЕ ССЫЛКИ ИЗ ОТВЕТА (на всякий случай)
                    import re
                    text = re.sub(r'#\s*\([^)]*\)', '', text)
                    text = re.sub(r'https?://\S+', '', text)
                    return text.strip()
                return f"Ошибка: {result}"
    except Exception as e:
        return f"Ошибка: {e}"
