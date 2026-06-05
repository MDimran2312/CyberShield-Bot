import os
import hashlib
import sqlite3
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---- ১. ডায়নামিক ল্যাঙ্গুয়েজ ও চ্যানেল কনফিগারেশন ----
# চ্যানেলগুলোর নাম বাংলা এবং ইংরেজি উভয় ভার্সনেই রাখা হয়েছে
CHANNELS = {
    'bn': [
        {"title": "📢 অফিশিয়াল চ্যানেল ১", "link": "https://t.me/fegasus_1"},
        {"title": "📢 অফিশিয়াল চ্যানেল ২", "link": "https://t.me/Falcon_Elite"},
        {"title": "📢 অফিশিয়াল চ্যানেল ৩", "link": "https://t.me/Cyber_Shield_official"}
    ],
    'en': [
        {"title": "📢 Official Channel 1", "link": "https://t.me/fegasus_1"},
        {"title": "📢 Official Channel 2", "link": "https://t.me/Falcon_Elite"},
        {"title": "📢 Official Channel 3", "link": "https://t.me/Cyber_Shield_official"}
    ]
}

LANG_TEXT = {
    'bn': {
        'welcome': "✨ <b>স্বাগতম!</b>\n\nনিচে আমাদের চ্যানেলগুলোতে জয়েন করুন এবং ভেরিফাই বাটনে ক্লিক করুন।",
        'verify': '✅ জয়েন করেছি (Verify)',
        'warning': "⚠️ {name}, কপি-পেস্ট করা নিষেধ! এটি আপনার {count}/৩ নম্বর ওয়ার্নিং।",
        'banned': "🚫 {name}, ৩ বার নিয়ম ভেঙেছেন, তাই ব্যান করা হলো!",
        'limit': "⚠️ {name}, ২৪ ঘণ্টায় ৮টির বেশি মেসেজ দেওয়া নিষেধ!"
    },
    'en': {
        'welcome': "✨ <b>Welcome!</b>\n\nPlease join our channels and click the verify button below.",
        'verify': '✅ I have joined',
        'warning': "⚠️ {name}, copying/pasting is forbidden! This is your {count}/3 warning.",
        'banned': "🚫 {name}, you have broken the rules 3 times and are banned!",
        'limit': "⚠️ {name}, sending more than 8 messages in 24 hours is not allowed!"
    }
}

API_TOKEN = '8709224461:AAEiDd1tQ20ql0teegS0WTR_MWeJymNJDDQ'
MAIN_ADMIN_ID = 8273597769

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ---- ডাটাবেজ সেটআপ ----
DB_PATH = os.path.join(os.path.dirname(__file__), 'group_security.db')
conn = sqlite3.connect(DB_PATH, timeout=20)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS msg_history (hash TEXT, user_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS user_lang (user_id INTEGER PRIMARY KEY, lang TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS user_msg_track (user_id INTEGER, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS user_warnings (user_id INTEGER PRIMARY KEY, count INTEGER)''')
conn.commit()

def get_user_lang(user_id):
    cursor.execute("SELECT lang FROM user_lang WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 'bn'

# ---- লজিক ----
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn"),
           InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"))
    await message.reply("ভাষা নির্বাচন করুন / Select Language:", reply_markup=kb)

@dp.callback_query_handler(lambda call: call.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery):
    lang = call.data.split("_")[1]
    cursor.execute("INSERT OR REPLACE INTO user_lang VALUES (?, ?)", (call.from_user.id, lang))
    conn.commit()
    
    kb = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS[lang]: kb.add(InlineKeyboardButton(text=ch["title"], url=ch["link"]))
    kb.add(InlineKeyboardButton(text=LANG_TEXT[lang]['verify'], callback_data="verify_user"))
    await call.message.edit_text(text=LANG_TEXT[lang]['welcome'], reply_markup=kb, parse_mode="HTML")

# ---- সিকিউরিটি ইঞ্জিন ----
@dp.message_handler(content_types=types.ContentType.ANY)
async def secure_group(message: types.Message):
    if message.chat.type == 'private' or message.from_user.is_bot: return
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status in ['administrator', 'creator']: return

    lang = get_user_lang(message.from_user.id)
    
    # ৬টি সিকিউরিটি সেটিং (লিংক, ফরওয়ার্ড, কপি-পেস্ট, লিমিট ইত্যাদি)
    if message.forward_from_chat or message.forward_from or any(x in str(message.text).lower() for x in ["http", "t.me/", "@"]):
        await message.delete(); return

    if message.text:
        text_hash = hashlib.md5(message.text.strip().encode('utf-8')).hexdigest()
        cursor.execute("SELECT user_id FROM msg_history WHERE hash=?", (text_hash,))
        row = cursor.fetchone()
        
        if row and row[0] != message.from_user.id:
            cursor.execute("SELECT count FROM user_warnings WHERE user_id=?", (message.from_user.id,))
            warn = cursor.fetchone()
            warn_count = warn[0] + 1 if warn else 1
            await message.delete()
            
            if warn_count >= 3:
                await bot.kick_chat_member(message.chat.id, message.from_user.id)
                await message.answer(LANG_TEXT[lang]['banned'].format(name=message.from_user.first_name))
                cursor.execute("DELETE FROM user_warnings WHERE user_id=?", (message.from_user.id,))
            else:
                await message.answer(LANG_TEXT[lang]['warning'].format(name=message.from_user.first_name, count=warn_count))
                cursor.execute("INSERT OR REPLACE INTO user_warnings VALUES (?, ?)", (message.from_user.id, warn_count))
            conn.commit(); return
        
        cursor.execute("INSERT INTO msg_history VALUES (?, ?)", (text_hash, message.from_user.id))
        
        # মেসেজ লিমিট (৮টি)
        limit_time = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM user_msg_track WHERE user_id=? AND timestamp > ?", (message.from_user.id, limit_time))
        if cursor.fetchone()[0] >= 8:
            await message.delete()
            await message.answer(LANG_TEXT[lang]['limit'].format(name=message.from_user.first_name))
            return
        cursor.execute("INSERT INTO user_msg_track VALUES (?, ?)", (message.from_user.id, datetime.now().isoformat()))
        conn.commit()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
