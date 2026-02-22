import aiosqlite

DB_NAME = "vestnik.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            title TEXT,
            style TEXT DEFAULT 'hardcore',
            topic_id INTEGER DEFAULT 1,
            enabled INTEGER DEFAULT 1,
            digest_hour INTEGER DEFAULT 20,
            digest_minute INTEGER DEFAULT 0
        )""")
        
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            chat_id INTEGER,
            nickname TEXT,
            description TEXT,
            gender TEXT,
            PRIMARY KEY (user_id, chat_id)
        )""")
        
        await db.execute("""CREATE TABLE IF NOT EXISTS processed_messages (
            chat_id INTEGER,
            message_id INTEGER,
            topic_id INTEGER,
            timestamp INTEGER,
            PRIMARY KEY (chat_id, message_id, topic_id)
        )""")
        await db.commit()

async def add_chat(chat_id: int, title: str, topic_id: int = 1):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO chats (chat_id, title, topic_id) VALUES (?, ?, ?)",
            (chat_id, title, topic_id)
        )
        await db.commit()

async def remove_chat(chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM chats WHERE chat_id=?", (chat_id,))
        await db.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
        await db.execute("DELETE FROM processed_messages WHERE chat_id=?", (chat_id,))
        await db.commit()

async def get_all_chats():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM chats WHERE enabled=1") as cursor:
            return await cursor.fetchall()

async def get_chat_config(chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM chats WHERE chat_id=?", (chat_id,)) as cursor:
            return await cursor.fetchone()

async def update_chat_topic(chat_id: int, topic_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE chats SET topic_id=? WHERE chat_id=?", (topic_id, chat_id))
        await db.commit()

async def update_chat_style(chat_id: int, style: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE chats SET style=? WHERE chat_id=?", (style, chat_id))
        await db.commit()

async def toggle_chat_enabled(chat_id: int, enabled: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE chats SET enabled=? WHERE chat_id=?", (enabled, chat_id))
        await db.commit()

async def update_chat_time(chat_id: int, hour: int, minute: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE chats SET digest_hour=?, digest_minute=? WHERE chat_id=?", 
                         (hour, minute, chat_id))
        await db.commit()

async def get_user_nickname(chat_id: int, user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT nickname FROM users WHERE user_id=? AND chat_id=?", 
            (user_id, chat_id)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def set_user_nickname(chat_id: int, user_id: int, nickname: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, chat_id, nickname) VALUES (?, ?, ?)",
            (user_id, chat_id, nickname)
        )
        await db.commit()

async def mark_message_processed(chat_id: int, message_id: int, topic_id: int, timestamp: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO processed_messages VALUES (?, ?, ?, ?)",
            (chat_id, message_id, topic_id, timestamp)
        )
        await db.commit()