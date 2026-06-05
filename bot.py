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
# ---- প্রয়োজনীয় ফাংশনসমূহ ----
def get_hash(text):
    return hashlib.md5(text.strip().encode('utf-8')).hexdigest()

async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in ['administrator', 'creator']

# ---- সিকিউরিটি ইঞ্জিন ----
@dp.message_handler(content_types=types.ContentType.ANY)
async def secure_group(message: types.Message):
    if message.chat.type == 'private' or message.from_user.is_bot: return
    
    # অ্যাডমিন চেক
    if await is_admin(message.chat.id, message.from_user.id):
        if message.text and len(message.text.strip()) > 4:
            cursor.execute("INSERT OR IGNORE INTO msg_history VALUES (?, ?)", (get_hash(message.text), message.from_user.id))
            conn.commit()
        return

    # ১. ফোর্স জয়েন চেক
    not_joined = await check_user_joined(message.from_user.id)
    if not_joined:
        try:
            await message.delete()
            keyboard = InlineKeyboardMarkup(row_width=1)
            for ch in CHANNELS['bn']:
                keyboard.add(InlineKeyboardButton(text=ch["title"], url=ch["link"]))
            await message.answer(f"⚠️ @{message.from_user.username}, চ্যানেলগুলোতে জয়েন না করলে মেসেজ দেওয়া যাবে না!", reply_markup=keyboard)
        except: pass
        return

    # ২. স্মার্ট ফরওয়ার্ড ফিল্টার
    if message.forward_from_chat and message.forward_from_chat.type in ['channel', 'supergroup']:
        await message.delete()
        await message.answer(f"❌ @{message.from_user.username}, পাবলিক চ্যানেল বা গ্রুপ থেকে ফরওয়ার্ড করা নিষেধ!")
        return

    # ৩. লিংক ও ইউজারনেম ফিল্টার
    if message.text:
        if any(x in message.text.lower() for x in ["http", "t.me/", "@"]):
            await message.delete()
            await message.answer(f"❌ @{message.from_user.username}, লিংক বা ইউজারনেম শেয়ার করা নিষেধ!")
            return

        # ৪. কপি-পেস্ট ফিল্টার
        clean_text = message.text.strip()
        if len(clean_text) <= 4: return

        text_hash = get_hash(clean_text)
        cursor.execute("SELECT hash FROM msg_history WHERE hash=?", (text_hash,))
        
        if cursor.fetchone():
            await message.delete()
            await bot.kick_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
            await message.answer(f"🚫 @{message.from_user.username} কে কপি-পেস্ট করার অপরাধে ব্যান করা হলো!")
        else:
            cursor.execute("INSERT OR IGNORE INTO msg_history VALUES (?, ?)", (text_hash, message.from_user.id))
            conn.commit()
            
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
