import os
import hashlib
import sqlite3
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---- ১. ল্যাঙ্গুয়েজ ও বিস্তারিত ওয়েলকাম মেসেজ ----
LANG_TEXT = {
    'bn': {
        'welcome': "✨ <b>স্বাগতম!</b>\n\nএই বোটটি ব্যবহার করতে নিচের ধাপগুলো অনুসরণ করুন:\n"
                   "১. প্রথমে আমাদের অফিসিয়াল চ্যানেলগুলোতে জয়েন করুন।\n"
                   "২. এরপর ভেরিফাই বাটনে ক্লিক করুন।\n"
                   "৩. সফল হলে বোটটিকে আপনার গ্রুপে অ্যাডমিন হিসেবে যুক্ত করুন।\n\n"
                   "<b>গ্রুপের নিয়মাবলী:</b>\n"
                   "- লিংক, ইউজারনেম বা স্প্যামিং নিষিদ্ধ।\n"
                   "- কপি-পেস্ট মেসেজ করলে ওয়ার্নিং পাবেন (৩বার ভুল করলে ব্যান)।\n"
                   "- ২৪ ঘণ্টায় সর্বোচ্চ ৮টি মেসেজ দেওয়া যাবে।",
        'verify': '✅ জয়েন করেছি (Verify)',
        'channels': 'আমাদের অফিসিয়াল চ্যানেলগুলোতে জয়েন করুন:',
        'success': "✅ <b>ভেরিফিকেশন সফল!</b>\n\nএখন নিচের বাটনে ক্লিক করে বোটটিকে আপনার গ্রুপে অ্যাডমিন হিসেবে যুক্ত করুন।"
    },
    'en': {
        'welcome': "✨ <b>Welcome!</b>\n\nFollow these steps:\n1. Join our official channels.\n2. Click the verify button.\n3. Add the bot to your group.\n\n<b>Rules:</b>\n- No links/usernames allowed.\n- Anti-copy-paste enabled (3 warnings then ban).\n- Max 8 messages per 24 hours.",
        'verify': '✅ I have joined',
        'channels': 'Please join our official channels:',
        'success': "✅ <b>Verification successful!</b>\n\nClick below to add the bot."
    }
}

API_TOKEN = '8709224461:AAEiDd1tQ20ql0teegS0WTR_MWeJymNJDDQ'
MAIN_ADMIN_ID = 8273597769

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

OFFICIAL_CHANNELS = [
    {"id": "-1003273901336", "title": "📢 চ্যানেল ১", "link": "https://t.me/fegasus_1"},
    {"id": "-1003698770950", "title": "📢 চ্যানেল ২", "link": "https://t.me/Falcon_Elite"},
    {"id": "-1003928674058", "title": "📢 চ্যানেল ৩", "link": "https://t.me/Cyber_Shield_official"}
]

# ---- ডাটাবেজ সেটআপ ----
DB_PATH = os.path.join(os.path.dirname(__file__), 'group_security.db')
conn = sqlite3.connect(DB_PATH, timeout=20)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS msg_history (hash TEXT, user_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS bot_users (user_id INTEGER PRIMARY KEY)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS user_lang (chat_id INTEGER PRIMARY KEY, lang TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS user_msg_track (user_id INTEGER, timestamp TEXT)''')
# ওয়ার্নিং কাউন্ট টেবিল
cursor.execute('''CREATE TABLE IF NOT EXISTS user_warnings (user_id INTEGER PRIMARY KEY, count INTEGER)''')
conn.commit()

def get_hash(text): return hashlib.md5(text.strip().encode('utf-8')).hexdigest()

async def is_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

async def check_user_joined(user_id):
    not_joined = []
    for ch in OFFICIAL_CHANNELS:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(ch)
        except: not_joined.append(ch)
    return not_joined

# ---- অ্যাডমিন প্যানেল ----
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != MAIN_ADMIN_ID: return
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("📊 মোট ইউজার", callback_data="admin_stats"),
                 InlineKeyboardButton("🗑️ হিস্ট্রি ক্লিয়ার", callback_data="clear_history"))
    await message.reply("👑 অ্যাডমিন প্যানেল", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data.startswith('admin_') or call.data == 'clear_history')
async def admin_callback(call: types.CallbackQuery):
    if call.data == "admin_stats":
        cursor.execute("SELECT COUNT(*) FROM bot_users")
        await call.answer(f"মোট ইউজার: {cursor.fetchone()[0]}", show_alert=True)
    elif call.data == "clear_history":
        cursor.execute("DELETE FROM msg_history")
        conn.commit()
        await call.answer("হিস্ট্রি ক্লিয়ার!", show_alert=True)

# ---- স্টার্ট কমান্ড ----
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if message.chat.type == 'private':
        cursor.execute("INSERT OR IGNORE INTO bot_users VALUES (?)", (message.from_user.id,))
        conn.commit()
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("🇧🇩 বাংলা", callback_data="set_lang_bn"),
                 InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en"))
    await message.reply("স্বাগতম! ভাষা নির্বাচন করুন / Select Language:", reply_markup=keyboard)

# ---- ভাষা ও চ্যানেল বাটন ----
@dp.callback_query_handler(lambda call: call.data.startswith("set_lang_"))
async def set_language(call: types.CallbackQuery):
    lang = call.data.split("_")[2]
    cursor.execute("INSERT OR REPLACE INTO user_lang VALUES (?, ?)", (call.from_user.id, lang))
    conn.commit()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in OFFICIAL_CHANNELS:
        keyboard.add(InlineKeyboardButton(text=ch["title"], url=ch["link"]))
    keyboard.add(InlineKeyboardButton(text=LANG_TEXT[lang]['verify'], callback_data="verify_user"))
    await call.message.edit_text(text=LANG_TEXT[lang]['welcome'], reply_markup=keyboard, parse_mode="HTML")

# ---- ভেরিফিকেশন ----
@dp.callback_query_handler(text="verify_user")
async def verify_user_callback(call: types.CallbackQuery):
    not_joined = await check_user_joined(call.from_user.id)
    if not_joined:
        await call.answer("⚠️ সব চ্যানেলে জয়েন করুন!", show_alert=True)
    else:
        await call.message.edit_text("⏳ যাচাই করা হচ্ছে...")
        await asyncio.sleep(1)
        lang = cursor.execute("SELECT lang FROM user_lang WHERE chat_id=?", (call.from_user.id,)).fetchone()
        l = lang[0] if lang else 'en'
        url = f"https://t.me/{(await bot.get_me()).username}?startgroup=true&admin=change_info+delete_messages+restrict_members"
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ গ্রুপে অ্যাড করুন", url=url))
        await call.message.edit_text(LANG_TEXT[l]['success'], reply_markup=kb, parse_mode="HTML")

# ---- সিকিউরিটি ও ওয়ার্নিং সিস্টেম ----
@dp.message_handler(content_types=types.ContentType.ANY)
async def secure_group(message: types.Message):
    if message.chat.type == 'private' or await is_admin(message.chat.id, message.from_user.id) or message.from_user.is_bot:
        return

    # ১. ফোর্স জয়েন, ২. ফরওয়ার্ড, ৩. লিংক কিলার
    if await check_user_joined(message.from_user.id) or message.forward_from_chat or message.forward_from or any(x in str(message.text).lower() for x in ["http", "t.me/", "@"]):
        await message.delete(); return

    # ৪. কপি-পেস্ট ও ওয়ার্নিং সিস্টেম
    if message.text:
        text_hash = get_hash(message.text.strip())
        cursor.execute("SELECT user_id FROM msg_history WHERE hash=?", (text_hash,))
        row = cursor.fetchone()
        
        if row and row[0] != message.from_user.id:
            cursor.execute("SELECT count FROM user_warnings WHERE user_id=?", (message.from_user.id,))
            warn = cursor.fetchone()
            warn_count = warn[0] + 1 if warn else 1
            
            if warn_count >= 3:
                await message.delete()
                await bot.kick_chat_member(message.chat.id, message.from_user.id)
                await message.answer(f"🚫 {message.from_user.first_name}, ৩ বার নিয়ম ভেঙেছেন, তাই ব্যান করা হলো!")
                cursor.execute("DELETE FROM user_warnings WHERE user_id=?", (message.from_user.id,))
            else:
                await message.delete()
                await message.answer(f"⚠️ {message.from_user.first_name}, কপি-পেস্ট নিষেধ! এটা আপনার {warn_count}/৩ ওয়ার্নিং।")
                cursor.execute("INSERT OR REPLACE INTO user_warnings VALUES (?, ?)", (message.from_user.id, warn_count))
            conn.commit()
            return
        
        cursor.execute("INSERT INTO msg_history VALUES (?, ?)", (text_hash, message.from_user.id))
        
        # ৫. মেসেজ লিমিট
        now = datetime.now().isoformat()
        limit_time = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM user_msg_track WHERE user_id=? AND timestamp > ?", (message.from_user.id, limit_time))
        if cursor.fetchone()[0] >= 8:
            await message.delete()
            return
        cursor.execute("INSERT INTO user_msg_track VALUES (?, ?)", (message.from_user.id, now))
        conn.commit()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
