from groq import AsyncGroq
import aiohttp
from config import SPONSOR_LINK, SPONSOR_TEXT
import os

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

STYLES = {
    'hardcore': """
ТЫ — АГРЕССИВНЫЙ, САТИРИЧЕСКИЙ ОБОЗРЕВАТЕЛЬ ЧАТА В СТИЛЕ "ВЕСТНИК ИНДИХУЯКЕР".

ПРАВИЛА:
1. ПИШИ С САРКАЗМОМ, ЮМОРОМ И СЛЕНГОМ.
2. ИСПОЛЬЗУЙ ВЫРАЖЕНИЯ: "видимо", "как истинный ценитель", "тут же окрестил", "наш местный", "доблестный рыцарь клавиатуры", "обосрался от", "бомбануло".
3. ОСКОРБЛЯЙ УЧАСТНИКОВ ЧАТА В ШУТОЧНОЙ ФОРМЕ. ВЫСМЕИВАЙ ИХ.
4. ДОБАВЛЯЙ ГИПЕРБОЛЫ: преувеличивай до абсурда.
5. ПИШИ ОТ 3 ДО 5 ПРЕДЛОЖЕНИЙ НА КАЖДЫЙ ПУНКТ.
6. В КОНЦЕ КАЖДОГО АБЗАЦА СТАВЬ ССЫЛКУ: # (https://t.me/c/{chat_link}/{topic_id}/{msg_id})

ПРИМЕРЫ СТИЛЯ:
- "Владис, наш доблестный рыцарь клавиатуры, решил блеснуть остроумием, обозвав Викторию «Мымрой старой»"
- "Бетономешалка не только VPN чинит, но и сердечные дела Юры налаживает, раз его так встретили"
- "Денис, со своими зауженками и подворотами, явно не соответствует стандартам «нормального мужика»"

ПИШИ ЖЁСТКО, САРКАСТИЧНО, С ДОПУСТИМЫМ МАТОМ. ТЫ НЕ МОДЕРАТОР, ТЫ САТИРИК.
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

async def generate_digest_text(messages: list, style: str = 'hardcore', chat_id: int = 0, sponsor_text: str = "", sponsor_link: str = ""):
    system_prompt = STYLES.get(style, STYLES['hardcore'])
    
    history = "\n".join([
        f"{msg['user']}: {msg['text']} {'[КАРТИНКА: ' + msg['image_desc'] + ']' if msg.get('image_desc') else ''}"
        for msg in messages
    ])
    
    chat_link = str(abs(chat_id)).replace('100', '')
    
    header = ""
    footer = ""
    if sponsor_text and sponsor_link:
        header = f"⭐️ Спонсор выпуска: {sponsor_text} ({sponsor_link})!\n\n"
        footer = f"\n⭐️ Спонсор выпуска: {sponsor_text} ({sponsor_link})!"
    
    prompt = f"""
{system_prompt}

ШАБЛОН ВЫВОДА:
{header}📰 Главное из последних 1000 сообщений, отправленных за последние 24 часа по чату:

# (ссылка) Текст...
# (ссылка) Текст...
(всего 9 пунктов)
{footer}

ИСТОРИЯ ЧАТА ДЛЯ АНАЛИЗА:
{history}

ВЫБЕРИ ТОП-9 САМЫХ ИНТЕРЕСНЫХ/СМЕШНЫХ/СКАНДАЛЬНЫХ МОМЕНТОВ И ОПИШИ ИХ В СТИЛЕ ВЫШЕ.
"""
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-70b-versatile",
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
            model="llama-3.1-70b-versatile",
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
