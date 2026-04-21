import aiosqlite

DB_NAME = "database.sqlite"
db = None # Global connection object

async def init_db():
    global db
    db = await aiosqlite.connect(DB_NAME)
    
    # Users table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            full_name TEXT,
            address TEXT,
            balance INTEGER DEFAULT 0,
            limit_count INTEGER DEFAULT 10,
            is_premium BOOLEAN DEFAULT FALSE,
            premium_start TIMESTAMP NULL,
            premium_end TIMESTAMP NULL,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            requests_count INTEGER DEFAULT 0
        )
    ''')
    # Movies table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            title TEXT,
            movie_type TEXT DEFAULT 'kino',
            file_id TEXT,
            duration TEXT DEFAULT '',
            coin_cost INTEGER DEFAULT 1
        )
    ''')
    # Mandatory Channels
    await db.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER UNIQUE,
            url TEXT,
            name TEXT,
            reward INTEGER DEFAULT 0
        )
    ''')
    # Applications table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            photo_id TEXT,
            plan_months INTEGER DEFAULT 1,
            app_type TEXT DEFAULT 'PREMIUM',
            amount INTEGER DEFAULT 0,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Transactions table (Financial logs)
    await db.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migrations for existing DB
    try:
        await db.execute("ALTER TABLE users ADD COLUMN last_active TIMESTAMP")
    except:
        pass
    try:
        await db.execute("ALTER TABLE users ADD COLUMN requests_count INTEGER DEFAULT 0")
    except:
        pass

    # Migration for applications
    try:
        await db.execute("ALTER TABLE applications ADD COLUMN app_type TEXT DEFAULT 'PREMIUM'")
    except:
        pass
    try:
        await db.execute("ALTER TABLE applications ADD COLUMN amount INTEGER DEFAULT 0")
    except:
        pass
    try:
        await db.execute("ALTER TABLE channels ADD COLUMN reward INTEGER DEFAULT 0")
    except:
        pass
    try:
        await db.execute("ALTER TABLE movies ADD COLUMN duration TEXT DEFAULT ''")
    except:
        pass
    # Rewarded Channels table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS rewarded_channels (
            user_id INTEGER,
            channel_url TEXT,
            PRIMARY KEY (user_id, channel_url)
        )
    ''')
        
    await db.commit()

async def close_db():
    global db
    if db:
        await db.close()

# --- Users ---
async def add_user(telegram_id: int, full_name: str, address: str = ""):
    await db.execute("INSERT OR IGNORE INTO users (telegram_id, full_name, address) VALUES (?, ?, ?)", 
                     (telegram_id, full_name, address))
    await db.commit()

async def get_user(telegram_id: int):
    async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
        return await cursor.fetchone()

async def update_user_activity(telegram_id: int):
    await db.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP, requests_count = requests_count + 1 WHERE telegram_id = ?", (telegram_id,))
    await db.commit()

async def get_statistics():
    async with db.execute("SELECT COUNT(*) FROM users") as cursor:
        total_users = (await cursor.fetchone())[0]
        
    async with db.execute("SELECT COUNT(*) FROM users WHERE last_active >= datetime('now', '-1 day')") as cursor:
        active_today = (await cursor.fetchone())[0]
        
    async with db.execute("SELECT SUM(requests_count) FROM users") as cursor:
        total_requests = (await cursor.fetchone())[0] or 0
        
    return total_users, active_today, total_requests

async def get_extended_statistics():
    # Premium foydalanuvchilar soni
    async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = TRUE") as cursor:
        premium_users = (await cursor.fetchone())[0]
        
    # Bugungi tushum (faqat musbat tranzaksiyalar - balans to'ldirishlar)
    async with db.execute("SELECT SUM(amount) FROM transactions WHERE date(date, 'localtime') = date('now', 'localtime') AND amount > 0") as cursor:
        daily_income = (await cursor.fetchone())[0] or 0
        
    # Jami tushum
    async with db.execute("SELECT SUM(amount) FROM transactions WHERE amount > 0") as cursor:
        total_income = (await cursor.fetchone())[0] or 0
        
    return premium_users, daily_income, total_income

async def get_all_users():
    async with db.execute("SELECT * FROM users") as cursor:
        return await cursor.fetchall()

async def update_user_balance(telegram_id: int, amount: int):
    await db.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (amount, telegram_id))
    await db.execute("INSERT INTO transactions (user_id, amount) VALUES (?, ?)", (telegram_id, amount))
    await db.commit()

async def decrement_limit(telegram_id: int, amount: int = 1):
    await db.execute("UPDATE users SET limit_count = limit_count - ? WHERE telegram_id = ? AND is_premium = FALSE AND limit_count >= ?", (amount, telegram_id, amount))
    await db.commit()

async def update_limit(telegram_id: int, amount: int):
    await db.execute("UPDATE users SET limit_count = ? WHERE telegram_id = ?", (amount, telegram_id))
    await db.commit()

async def set_premium(telegram_id: int, status: bool, days: int = 30):
    if status:
        await db.execute("""
            UPDATE users SET 
            is_premium = TRUE, 
            premium_start = CURRENT_TIMESTAMP,
            premium_end = datetime('now', '+' || ? || ' days')
            WHERE telegram_id = ?
        """, (days, telegram_id))
    else:
        await db.execute("UPDATE users SET is_premium = FALSE, premium_start = NULL, premium_end = NULL WHERE telegram_id = ?", (telegram_id,))
    await db.commit()

async def check_and_update_premium(telegram_id: int):
    """Premium muddati tugagan bo'lsa uni o'chirish"""
    async with db.execute("SELECT premium_end FROM users WHERE telegram_id = ? AND is_premium = TRUE", (telegram_id,)) as cursor:
        row = await cursor.fetchone()
        if row and row[0]:
            from datetime import datetime
            try:
                # SQLite TIMESTAMP formatini parse qilish (turli formatlar bo'lishi mumkin)
                p_end_str = row[0].split('.')[0] # '2024-04-20 12:00:00'
                p_end = datetime.strptime(p_end_str, '%Y-%m-%d %H:%M:%S')
                if p_end < datetime.now():
                    await set_premium(telegram_id, False)
                    return False
                return True
            except Exception as e:
                print(f"Premium check error: {e}")
    return False
    
# --- Applications (Payment Proofs) ---
async def add_application(user_id: int, full_name: str, photo_id: str, plan_months: int = 1, app_type: str = 'PREMIUM', amount: int = 0):
    cursor = await db.execute("INSERT INTO applications (user_id, full_name, photo_id, plan_months, app_type, amount) VALUES (?, ?, ?, ?, ?, ?)", 
                     (user_id, full_name, photo_id, plan_months, app_type, amount))
    await db.commit()
    return cursor.lastrowid

async def get_pending_applications():
    async with db.execute("SELECT * FROM applications WHERE status = 'PENDING'") as cursor:
        return await cursor.fetchall()

async def update_application_status(app_id: int, status: str):
    await db.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
    await db.commit()

async def get_application(app_id: int):
    async with db.execute("SELECT * FROM applications WHERE id = ?", (app_id,)) as cursor:
        return await cursor.fetchone()

# --- Movies ---
async def add_movie(code: str, title: str, movie_type: str, file_id: str, duration: str = "", coin_cost: int = 1):
    try:
        await db.execute(
            "INSERT INTO movies (code, title, movie_type, file_id, duration, coin_cost) VALUES (?, ?, ?, ?, ?, ?)",
            (code, title, movie_type, file_id, duration, coin_cost)
        )
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False # Code already exists

async def get_movie(code: str):
    async with db.execute("SELECT * FROM movies WHERE code = ?", (code,)) as cursor:
        return await cursor.fetchone()

async def search_movie_by_title(title: str):
    async with db.execute("SELECT * FROM movies WHERE title LIKE ?", ('%'+title+'%',)) as cursor:
        return await cursor.fetchall()
        
async def delete_movie(code: str):
    await db.execute("DELETE FROM movies WHERE code = ?", (code,))
    await db.commit()

# --- Channels ---
async def add_channel(channel_id: int, url: str, name: str, reward: int = 0):
    try:
        await db.execute("INSERT INTO channels (channel_id, url, name, reward) VALUES (?, ?, ?, ?)", (channel_id, url, name, reward))
        await db.commit()
        return True
    except:
        return False

async def get_channels():
    async with db.execute("SELECT * FROM channels") as cursor:
        return await cursor.fetchall()

async def remove_channel(channel_id: int):
    await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    await db.commit()

# --- Customer Management Queries ---

async def get_active_premiums():
    async with db.execute("""
        SELECT * FROM users 
        WHERE is_premium = TRUE AND (premium_end > CURRENT_TIMESTAMP OR premium_end IS NULL)
    """) as cursor:
        return await cursor.fetchall()

async def get_expired_premiums():
    async with db.execute("""
        SELECT * FROM users 
        WHERE is_premium = TRUE AND premium_end <= CURRENT_TIMESTAMP
    """) as cursor:
        return await cursor.fetchall()

async def get_users_paged(offset: int = 0, limit: int = 10):
    async with db.execute("SELECT * FROM users LIMIT ? OFFSET ?", (limit, offset)) as cursor:
        users = await cursor.fetchall()
    async with db.execute("SELECT COUNT(*) FROM users") as cursor:
        total = (await cursor.fetchone())[0]
    return users, total

async def get_approved_applications():
    async with db.execute("SELECT * FROM applications WHERE status = 'APPROVED' ORDER BY created_at DESC") as cursor:
        return await cursor.fetchall()

async def get_user_spent_amount(telegram_id: int):
    async with db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND amount < 0", (telegram_id,)) as cursor:
        row = await cursor.fetchone()
        return abs(row[0]) if row and row[0] else 0

# --- Earning / Rewards ---
async def is_channel_rewarded(user_id: int, channel_url: str):
    async with db.execute("SELECT 1 FROM rewarded_channels WHERE user_id = ? AND channel_url = ?", (user_id, channel_url)) as cursor:
        return await cursor.fetchone() is not None

async def add_channel_reward(user_id: int, channel_url: str):
    await db.execute("INSERT OR IGNORE INTO rewarded_channels (user_id, channel_url) VALUES (?, ?)", (user_id, channel_url))
    await db.commit()
