import os
import hashlib
import sqlite3
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ---- ১. ল্যাঙ্গুয়েজ ও চ্যানেল কনফিগারেশন ----
CHANNELS = {
    'bn': [
        {"id": "-1003273901336", "title": "📢 অফিশিয়াল চ্যানেল ১", "link": "https://t.me/fegasus_1"},
        {"id": "-1003698770950", "title": "📢 অফিশিয়াল চ্যানেল ২", "link": "https://t.me/Falcon_Elite"},
        {"id": "-1003928674058", "title": "📢 অফিশিয়াল চ্যানেল ৩", "link": "https://t.me/Cyber_Shield_official"}
    ],
    'en': [
        {"id": "-1003273901336", "title": "📢 Official Channel 1", "link": "https://t.me/fegasus_1"},
        {"id": "-1003698770950", "title": "📢 Official Channel 2", "link": "https://t.me/Falcon_Elite"},
        {"id": "-1003928674058", "title": "📢 Official Channel 3", "link": "https://t.me/Cyber_Shield_official"}
    ]
}

LANG_TEXT = {
    'bn': {
        'welcome': "✨ <b>স্বাগতম!</b>\n\nনিচে আমাদের চ্যানেলগুলোতে জয়েন করুন এবং ভেরিফাই বাটনে ক্লিক করুন।",
        'verify': '✅ জয়েন করেছি (Verify)',
        'success': "✅ <b>ভেরিফিকেশন সফল!</b>\n\nএখন বোটটিকে গ্রুপে অ্যাডমিন হিসেবে যুক্ত করুন।",
        'warning': "⚠️ {name}, কপি-পেস্ট করা নিষেধ! এটি আপনার {count}/৩ নম্বর ওয়ার্নিং।",
        'banned': "🚫 {name}, ৩ বার নিয়ম ভেঙেছেন, তাই ব্যান করা হলো!",
        'limit': "⚠️ {name}, ২৪ ঘণ্টায় ৮টির বেশি মেসেজ দেওয়া নিষেধ!"
    },
    'en': {
        'welcome': "✨ <b>Welcome!</b>\n\nPlease join our channels and click the verify button below.",
        'verify': '✅ I have joined',
        'success': "✅ <b>Verification successful!</b>\n\nNow add the bot to your group as an admin.",
        'warning': "⚠️ {name}, copying/pasting is forbidden! This is your {count}/3 warning.",
        'banned': "🚫 {name}, you have broken the rules 3 times and are banned!",
        'limit': "⚠️ {name}, sending more than 8 messages in 24 hours is not allowed!"
    }
}

API_TOKEN = '8709224461:AAEiDd1tQ20ql0teegS0WTR_MWeJymNJDDQ'
MAIN_ADMIN_ID = 8273597769

class BroadcastState(StatesGroup):
    waiting_for_message = State()

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# ---- ডাটাবেজ সেটআপ ----
DB_PATH = os.path.join(os.path.dirname(__file__), 'group_security.db')
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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

async def check_user_joined(user_id):
    for ch in CHANNELS['bn']:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status not in ['member', 'administrator', 'creator']: return True
        except: return True
    return False

# ---- অ্যাডমিন প্যানেল ----
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != MAIN_ADMIN_ID: return
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("📊 মোট ইউজার", callback_data="admin_stats"),
           InlineKeyboardButton("🗑️ হিস্ট্রি ক্লিয়ার", callback_data="admin_clear"),
           InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data="admin_broadcast"))
    await message.reply("👑 অ্যাডমিন প্যানেল", reply_markup=kb)

@dp.callback_query_handler(lambda call: call.data.startswith("admin_"))
async def admin_callback(call: types.CallbackQuery):
    if call.data == "admin_clear":
        cursor.execute("DELETE FROM msg_history")
        conn.commit()
        await call.answer("হিস্ট্রি ক্লিয়ার করা হয়েছে!", show_alert=True)
    elif call.data == "admin_stats":
        cursor.execute("SELECT COUNT(*) FROM user_lang")
        count = cursor.fetchone()[0]
        await call.answer(f"মোট ইউজার: {count}", show_alert=True)
    elif call.data == "admin_broadcast":
        await call.message.answer("📢 ব্রডকাস্ট মেসেজটি লিখুন:")
        await BroadcastState.waiting_for_message.set()

@dp.message_handler(state=BroadcastState.waiting_for_message)
async def process_broadcast(message: types.Message, state: FSMContext):
    cursor.execute("SELECT user_id FROM user_lang")
    users = cursor.fetchall()
    count = 0
    for u in users:
        try:
            await bot.send_message(u[0], message.text, parse_mode="HTML")
            count += 1
            await asyncio.sleep(0.1)
        except: continue
    await message.reply(f"✅ {count} জনকে মেসেজ পাঠানো হয়েছে।")
    await state.finish()

# ---- স্টার্ট ও ল্যাঙ্গুয়েজ ----
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

@dp.callback_query_handler(text="verify_user")
async def verify_user_callback(call: types.CallbackQuery):
    if await check_user_joined(call.from_user.id):
        await call.answer("⚠️ সব চ্যানেলে জয়েন করুন!", show_alert=True)
    else:
        await call.message.edit_text("⏳ যাচাই করা হচ্ছে...")
        await asyncio.sleep(1)
        lang = get_user_lang(call.from_user.id)
        url = f"https://t.me/{(await bot.get_me()).username}?startgroup=true&admin=change_info+delete_messages+restrict_members"
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ গ্রুপে অ্যাড করুন", url=url))
        await call.message.edit_text(LANG_TEXT[lang]['success'], reply_markup=kb, parse_mode="HTML")

# ---- সিকিউরিটি ইঞ্জিন ----
@dp.message_handler(content_types=types.ContentType.ANY)
async def secure_group(message: types.Message):
    # ১. এডমিন ও বোটের জন্য সুরক্ষা (এডমিনদের কোনো বিধিনিষেধ নেই)
    if message.chat.type == 'private' or message.from_user.is_bot: return
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status in ['administrator', 'creator']: return

    lang = get_user_lang(message.from_user.id)
    
    # ২. ফোর্স জয়েন চেক (চ্যানেলে জয়েন না থাকলে মেসেজ ডিলিট)
    if await check_user_joined(message.from_user.id):
        await message.delete(); return

    # ৩. লিংক ও ইউজারনেম কিলার (লিংক বা @username দিলে ওয়ার্নিং দিবে, ব্যান করবে না)
    if message.text and (any(x in str(message.text).lower() for x in ["http", "t.me/", "www.", ".com"]) or "@" in message.text):
        await message.delete()
        await message.answer(LANG_TEXT[lang]['link_warn'].format(name=message.from_user.first_name))
        return

    # ৪. কপি-পেস্ট ও ওয়ার্নিং সিস্টেম (২ বার ওয়ার্নিং, ৩য় বারে অটো ব্যান)
    if message.text:
        text_hash = hashlib.md5(message.text.strip().encode('utf-8')).hexdigest()
        cursor.execute("SELECT user_id FROM msg_history WHERE hash=?", (text_hash,))
        row = cursor.fetchone()
        
        # যদি অন্য কারো মেসেজ কপি করা হয়
        if row and row[0] != message.from_user.id:
            await message.delete() # কপি করা মেসেজ ডিলিট
            
            cursor.execute("SELECT count FROM user_warnings WHERE user_id=?", (message.from_user.id,))
            warn = cursor.fetchone()
            warn_count = (warn[0] + 1) if warn else 1
            
            # ৩য় বার নিয়ম ভাঙলে ব্যান
            if warn_count >= 3:
                await bot.kick_chat_member(message.chat.id, message.from_user.id)
                await message.answer(LANG_TEXT[lang]['banned'].format(name=message.from_user.first_name))
                cursor.execute("DELETE FROM user_warnings WHERE user_id=?", (message.from_user.id,))
            else:
                # ওয়ার্নিং নোটিশ
                await message.answer(LANG_TEXT[lang]['warning'].format(name=message.from_user.first_name, count=warn_count))
                cursor.execute("INSERT OR REPLACE INTO user_warnings VALUES (?, ?)", (message.from_user.id, warn_count))
            
            conn.commit(); return
        
        # ইউনিক মেসেজ হিসেবে সেভ করুন
        cursor.execute("INSERT INTO msg_history VALUES (?, ?)", (text_hash, message.from_user.id))
        
        # ৫. ২৪ ঘণ্টায় ৮টি মেসেজ লিমিট
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
