import os
import hashlib
import os
import hashlib
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ---- ⚙️ বোট কনফিগারেশন ----
API_TOKEN = '8709224461:AAEiDd1tQ20ql0teegS0WTR_MWeJymNJDDQ'  # এখানে আপনার আসল বোট টোকেনটি বসান
MAIN_ADMIN_ID = 8273597769        # আপনার মেইন অ্যাডমিন আইডি

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ---- ৩টি অফিশিয়াল চ্যানেলের কনফিগারেশন ----
OFFICIAL_CHANNELS = [
    {"id": "-1003273901336", "title": "📢 অফিশিয়াল চ্যানেল ১", "link": "https://t.me/fegasus_1"},
    {"id": "-1003698770950", "title": "📢 অফিশিয়াল চ্যানেল ২", "link": "https://t.me/Falcon_Elite"},
    {"id": "-1003928674058", "title": "📢 অফিশিয়াল চ্যানেল ৩", "link": "https://t.me/Cyber_Shield_official"}
]

# ---- ডাটাবেজ সেটআপ (Railway Persistent Path) ----
# রেলওয়েতে ফাইল রিস্টার্ট এড়াতে /tmp/ বা ডিরেক্ট কারেন্ট ডিরেক্টরি পাথ নিশ্চিত করা
DB_PATH = os.path.join(os.path.dirname(__file__), 'group_security.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS msg_history (hash TEXT PRIMARY KEY)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS bot_users (user_id INTEGER PRIMARY KEY)''')
conn.commit()

def get_hash(text):
    return hashlib.md5(text.strip().encode('utf-8')).hexdigest()

async def is_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except Exception:
        return False

async def check_user_joined(user_id):
    not_joined = []
    for ch in OFFICIAL_CHANNELS:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(ch)
        except Exception:
            # চ্যানেল থেকে রেসপন্স না পেলে বা বোট অ্যাডমিন না থাকলে স্কিপ করবে
            continue
    return not_joined

# ---- 🎛️ ১. অ্যাডমিন প্যানেল কমান্ড (/admin) ----
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM bot_users")
    total_users = cursor.fetchone()[0]

    admin_keyboard = InlineKeyboardMarkup(row_width=1)
    admin_keyboard.add(
        InlineKeyboardButton(text="📊 বোটের তথ্য (Stats)", callback_data="admin_stats"),
        InlineKeyboardButton(text="🗑️ কপি-পেস্ট ডাটা ক্লিয়ার করুন", callback_data="clear_history"),
        InlineKeyboardButton(text="📢 ব্রডকাস্ট মেসেজ পাঠান", callback_data="admin_broadcast_info")
    )

    await message.reply(
        f"👑 **স্বাগতম, মেইন অ্যাডমিন!**\n\n"
        f"📱 বোটের বর্তমান ইউজার সংখ্যা: `{total_users}` জন\n"
        f"নিচের বাটনগুলো ব্যবহার করে বোট কন্ট্রোল করুন।",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )

# ---- অ্যাডমিন প্যানেল বাটন লজিক ----
@dp.callback_query_handler(lambda call: call.data.startswith('admin_') or call.data == 'clear_history')
async def admin_callback_handler(call: types.CallbackQuery):
    if call.from_user.id != MAIN_ADMIN_ID:
        await call.answer("❌ আপনি এই বোটের মেইন অ্যাডমিন নন!", show_alert=True)
        return

    if call.data == "admin_stats":
        cursor.execute("SELECT COUNT(*) FROM bot_users")
        total_users = cursor.fetchone()[0]
        await call.answer(f"📊 মোট বোট ইউজার: {total_users} জন", show_alert=True)

    elif call.data == "clear_history":
        cursor.execute("DELETE FROM msg_history")
        conn.commit()
        await call.answer("🗑️ কপি-পেস্টের আগের সব ডাটা সফলভাবে মুছে ফেলা হয়েছে!", show_alert=True)

    elif call.data == "admin_broadcast_info":
        await call.answer("📢 ব্রডকাস্ট করতে চ্যাটে লিখুন: /broadcast আপনার মেসেজ", show_alert=True)

# ---- ২. স্টার্ট কমান্ড ----
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    bot_user = await bot.get_me()
    
    if message.chat.type == 'private':
        cursor.execute("INSERT OR IGNORE INTO bot_users VALUES (?)", (user_id,))
        conn.commit()
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in OFFICIAL_CHANNELS:
        keyboard.add(InlineKeyboardButton(text=ch["title"], url=ch["link"]))
    
    keyboard.add(InlineKeyboardButton(text="✅ জয়েন করেছি (Verify)", callback_data="verify_user"))
    add_to_group_url = f"https://t.me/{bot_user.username}?startgroup=true"
    keyboard.add(InlineKeyboardButton(text="➕ বোটটি আপনার গ্রুপে অ্যাড করুন", url=add_to_group_url))

    welcome_text = (
        f"👋 **হ্যালো {message.from_user.first_name}!**\n\n"
        "🛡️ এটি একটি উন্নত **টেলিগ্রাম গ্রুপ সিকিউরিটি বোট**।\n\n"
        "⚠️ **বোটটি সচল করতে প্রথমে নিচে দেওয়া আমাদের ৩টি অফিশিয়াল চ্যানেলে জয়েন করুন,** "
        "তারপর নিচে থাকা **'জয়েন করেছি'** বাটনে ক্লিক করুন।"
    )
    await message.reply(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

# ---- ৩. জয়েন ভেরিফিকেশন ----
@dp.callback_query_handler(text="verify_user")
async def verify_user_callback(call: types.CallbackQuery):
    not_joined = await check_user_joined(call.from_user.id)
    
    if not_joined:
        await call.answer("⚠️ আপনি এখনও সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে সবগুলোতে জয়েন করুন।", show_alert=True)
    else:
        await call.answer("✅ ভেরিফিকেশন সফল হয়েছে!", show_alert=True)
        
        bot_user = await bot.get_me()
        success_keyboard = InlineKeyboardMarkup(row_width=1)
        add_to_group_url = f"https://t.me/{bot_user.username}?startgroup=true"
        success_keyboard.add(InlineKeyboardButton(text="➕ বোটটি এখনই আপনার গ্রুপে অ্যাড করুন", url=add_to_group_url))
        
        await call.message.edit_text(
            "🎉 **অভিনন্দন! আপনার ভেরিফিকেশন সফল হয়েছে।**\n\n"
            "এই সিকিউরিটি বোটটি এখন আপনার নিজের গ্রুপের জন্য প্রস্তুত। "
            "নিচে দেওয়া ইনলাইন বাটনে ক্লিক করে বোটটি এখনই আপনার গ্রুপে অ্যাড করে নিন এবং গ্রুপের সিকিউরিটি ১০০% মজবুত করুন!\n\n"
            "*(নোট: গ্রুপে অ্যাড করার পর বোটটিকে অবশ্যই Admin বানিয়ে অল পারমিশন দিয়ে দেবেন।)*",
            reply_markup=success_keyboard,
            parse_mode="Markdown"
        )

# ---- 📢 ৪. ব্রডকাস্ট কমান্ড ----
@dp.message_handler(commands=['broadcast'])
async def broadcast_message(message: types.Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return

    broadcast_text = message.get_args()
    if not broadcast_text:
        await message.reply("⚠️ ব্রডকাস্ট করার জন্য কিছু লিখুন!")
        return

    cursor.execute("SELECT user_id FROM bot_users")
    users = cursor.fetchall()
    
    status_msg = await message.reply(f"⏳ {len(users)} জন ইউজারের কাছে মেসেজ পাঠানো শুরু হচ্ছে...")
    success_count = 0
    fail_count = 0
    
    for (user_id,) in users:
        try:
            await bot.send_message(chat_id=user_id, text=broadcast_text)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1

    await status_msg.edit_text(
        f"✅ **ব্রডকাস্ট সম্পন্ন হয়েছে!**\n\n"
        f"🚀 সফলভাবে গিয়েছে: {success_count} জনের কাছে\n"
        f"❌ ব্যর্থ হয়েছে: {fail_count} জন"
    )

# ---- ৫. মূল সিকিউরিটি ও গ্রুপ প্রটেকশন ----
@dp.message_handler(content_types=types.ContentType.ANY)
async def secure_group(message: types.Message):
    if message.chat.type == 'private':
        return

    # কমান্ড বা বোটের নিজস্ব মেসেজ ফিল্টার করা (যাতে এগুলো কপি-পেস্ট ডাটাবেজে না যায়)
    if message.text and (message.text.startswith('/') or message.from_user.is_bot):
        return

    if await is_admin(message.chat.id, message.from_user.id):
        if message.text:
            cursor.execute("INSERT OR IGNORE INTO msg_history VALUES (?)", (get_hash(message.text),))
            conn.commit()
        return

    # ফোর্স জয়েন চেক
    not_joined = await check_user_joined(message.from_user.id)
    if not_joined:
        try:
            await message.delete()
            keyboard = InlineKeyboardMarkup(row_width=1)
            for ch in not_joined:
                keyboard.add(InlineKeyboardButton(text=ch["title"], url=ch["link"]))
            await message.answer(f"⚠️ @{message.from_user.username}, গ্রুপে মেসেজ দিতে আমাদের অফিশিয়াল চ্যানেলগুলোতে জয়েন করুন!", reply_markup=keyboard)
        except Exception:
            pass
        return

    # ফরওয়ার্ড ফিল্টার
    if message.forward_from_chat:
        if message.forward_from_chat.username:
            try:
                await message.delete()
                await message.answer(f"❌ @{message.from_user.username}, পাবলিক চ্যানেল বা গ্রুপ থেকে পোস্ট ফরওয়ার্ড করা নিষেধ!")
            except Exception:
                pass
            return

    # লিংক ও ইউজারনেম ফিল্টার
    if message.text:
        if "t.me/" in message.text or "@" in message.text:
            try:
                await message.delete()
            except Exception:
                pass
            return

        # কপি-পেস্ট অ্যান্ড ব্যান সেটিং
        text_hash = get_hash(message.text)
        cursor.execute("SELECT hash FROM msg_history WHERE hash=?", (text_hash,))
        
        if cursor.fetchone():
            try:
                await message.delete()
                await bot.kick_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
                
                warning_text = (
                    f"🚨 **কপি-পেস্ট অ্যালার্ট ও ব্যান নোটিশ!** 🚨\n\n"
                    f"👤 **ইউজার:** @{message.from_user.username}\n"
                    f"🆔 **আইডি:** `{message.from_user.id}`\n\n"
                    f"❌ **অপরাধ:** এই গ্রুপে থাকা অন্য কোনো ইউজারের আসল/প্রথম পোস্টটি হুবহু কপি করে পেস্ট করার চেষ্টা করা হয়েছে।\n\n"
                    f"📢 **অ্যাকশন:** গ্রুপের নিয়ম ভঙ্গ করায় ইউজারকে গ্রুপ থেকে **ব্যান (Ban)** করা হলো!"
                )
                await message.answer(warning_text, parse_mode="Markdown")
            except Exception as e:
                print(f"ব্যান বা মেসেজ ডিলিট করতে সমস্যা হয়েছে: {e}")
        else:
            cursor.execute("INSERT OR IGNORE INTO msg_history VALUES (?)", (text_hash,))
            conn.commit()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
