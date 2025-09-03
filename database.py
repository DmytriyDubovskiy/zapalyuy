import aiosqlite

async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                age_verified INTEGER,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Psychologists table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS psychologists(
                user_id INTEGER PRIMARY KEY
            )
        """)

        # Consultations table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS consultations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                psychologist_id INTEGER,
                scheduled_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'request',
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Feedback table
        await db.execute("""CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Create indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_consult_status ON consultations(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_consult_time ON consultations(scheduled_time)")
        await db.commit()

async def add_psychologist_to_db(user_id: int):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO psychologists (user_id) VALUES (?)", 
            (user_id,)
        )
        await db.commit()


async def remove_psychologist_from_db(user_id: int):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute(
            "DELETE FROM psychologists WHERE user_id = ?", 
            (user_id,)
        )
        await db.commit()
