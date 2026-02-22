from groq import AsyncGroq
import aiohttp
import os

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

STYLES = {
    'hardcore': """
ТЫ — АГРЕССИВНЫЙ, САТИРИЧЕСКИЙ ОБОЗРЕВАТЕЛЬ ЧАТА В СТИЛЕ "ВЕСТНИК ИНДИХУЯКЕР".

ПРАВИЛА:
1. Пиши с сарказмом, юмором и сленгом.
2. Используй выражения: "видимо", "как истинный ценитель", "тут же окрестил", "наш местный", "доблестный рыцарь клавиатуры", "обосрался от", "бомбануло".
3. Осмеивай участников чата в шуточной форме. Высмеивай их.
4. Добавляй гиперболы: преувеличивай до абсурда.
5. Пиши от 3 до 5 предложений на каждый пункт.
6. В конце каждого абзаца ставь ссылку: # (https://t.me/c/{chat_link}/{topic_id}/{msg_id})

ПРИМЕРЫ СТИЛЯ:
- "Владис, наш доблестный рыцарь клавиатуры, решил блеснуть остроумием, обозвав Викторию «Мымрой старой»"
- "Бетономешалка не только VPN чинит, но и сердечные дела Юры налаживает, раз его так встретили"
- "Денис, со своими зауженками и подворотами, явно не соответствует стандартам «нормального мужика»"

Пиши жёстко, саркастично, в стиле оригинального Вестника. Ты не модератор, ты сатирик.
""",
    
    'classic': "Ты сатирический обозреватель. Пиши с юмором и сарказмом, можно умеренный мат.",
    'neutral': "Ты нейтральный наблюдатель. Пиши без мата, вежливо.",
    'love': "Ты добрый друг. Хвали всех, никаких оскорблений.",
    'custom': "Ты пишешь в свободном стиле с сарказмом и юмором."
}

async def describe_image(image_url: str) -> str:
    try:
        url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                image_data = await resp.read()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=image_data) as resp:
                result = await resp.json()
                return result[0]['generated_text'] if result else "Картинка"
    except:
        return "Картинка (не распознано)"

async def generate_digest_text(messages: list, style: str = 'hardcore', chat_id: int = 0):
    system_prompt = STYLES.get(style, STYLES['hardcore'])
    
    history = "\n".join([
        f"{msg['user']}: {msg['text']} {'[КАРТИНКА: ' + msg['image_desc'] + ']' if msg.get('image_desc') else ''}"
        for msg in messages
    ])
    
    chat_link = str(abs(chat_id)).replace('100', '')
    
    prompt = f"""
{system_prompt}

ШАБЛОН ВЫВОДА:
📰 Главное из последних 1000 сообщений, отправленных за последние 24 часа по чату:

# (ссылка) Текст...
# (ссылка) Текст...
(всего 9 пунктов)

ИСТОРИЯ ЧАТА ДЛЯ АНАЛИЗА:
{history}

ВЫБЕРИ ТОП-9 САМЫХ ИНТЕРЕСНЫХ/СМЕШНЫХ/СКАНДАЛЬНЫХ МОМЕНТОВ И ОПИШИ ИХ В СТИЛЕ ВЫШЕ.
"""
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Модель стабильнее и бесплатна
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка ИИ: {e}"

async def ai_answer(question: str, context: str, style: str):
    system_prompt = STYLES.get(style, STYLES['hardcore'])
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"{system_prompt}\nКонтекст: {context}"},
                {"role": "user", "content": question}
            ],
            temperature=0.9,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"
