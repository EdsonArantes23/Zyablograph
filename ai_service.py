from groq import AsyncGroq
import aiohttp
from config import SPONSOR_LINK, SPONSOR_TEXT

client = AsyncGroq()

STYLES = {
    'hardcore': "Ты агрессивный саркастичный модератор чата. Пиши с матом, оскорблениями, сарказмом, сленгом. Высмеивай участников, будь жёстким, используй выражения типа 'видимо', 'как истинный ценитель', 'тут же окрестил'.",
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
Ты — сатирический обозреватель чата. Твоя задача: проанализировать последние сообщения и написать дайджест.

ПРАВИЛА:
1. Выбери топ-9 самых интересных/смешных моментов из истории.
2. Для каждого напиши абзац (3-5 предложений) с сарказмом, юмором и сленгом.
3. В конце каждого абзаца ставь ссылку: # (https://t.me/c/{chat_link}/{msg['topic_id']}/{msg['id']})
4. Используй мат и оскорбления если это уместно в стиле.
5. Добавь шапку в начале.

ШАБЛОН:
{header}📰 Главное из последних 1000 сообщений, отправленных за последние 24 часа по чату:

# (ссылка) Текст...
# (ссылка) Текст...
{footer}

ИСТОРИЯ ЧАТА:
{history}
"""
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
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
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"