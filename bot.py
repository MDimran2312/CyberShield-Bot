import os
import hashlib
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# ১. ল্যাঙ্গুয়েজ সেটিংস
LANG_TEXT = {
        'bn': {
        'verify_alert': "⚠️ দুঃখিত!\n\nআপনি এখনো সবগুলোতে জয়েন করেননি। অনুগ্রহ করে সব চ্যানেলগুলোতে জয়েন করে আবার ট্রাই করুন।",
        'success_text': "✅ <b>ভেরিফিকেশন সফল হয়েছে!</b>\n\nধন্যবাদ আমাদের চ্যানেলগুলোতে জয়েন করার জন্য। এখন নিচের বাটনটি ক্লিক করে বোটটিকে আপনার গ্রুপে যুক্ত করুন।",
        'verify': '✅ জয়েন করেছি (Verify)',
        'channels': 'আমাদের অফিসিয়াল চ্যানেলগুলোতে জয়েন করুন:',  # <--- এখানে কমা যোগ করো
        'welcome_msg': "✨ <b>স্বাগতম!</b>\n\nএই গ্রুপে লিংক বা ইউজারনেম শেয়ার করা সম্পূর্ণ নিষিদ্ধ। অনুগ্রহ করে নিয়ম মেনে চলুন।"
    },
    'en': {
        'verify_alert': "⚠️ Oops!\n\nYou haven't joined all channels yet. Please join all channels and try again.",
        'success_text': "✅ <b>Verification Successful!</b>\n\nThank you for joining our channels. Now click the button below to add the bot to your group.",
        'verify': '✅ I have joined',
        'channels': 'Please join our official channels:',  # <--- এখানে কমা যোগ করো
        'welcome_msg': "✨ <b>Welcome!</b>\n\nSharing links or usernames in this group is strictly prohibited. Please follow the rules."
    }
} #

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

# ---- ডাটাবেজ সেটআপ ----
DB_PATH = os.path.join(os.path.dirname(__file__), 'group_security.db')
conn = sqlite3.connect(DB_PATH, timeout=20)
cursor = conn.cursor()

# টেবিলগুলো তৈরি করার সঠিক সিকোয়েন্স
cursor.execute('''CREATE TABLE IF NOT EXISTS msg_history (hash TEXT PRIMARY KEY)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS bot_users (user_id INTEGER PRIMARY KEY)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS user_lang (chat_id INTEGER PRIMARY KEY, lang TEXT)''')

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
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return not_joined

# ---- 🤝 গ্রুপে অটো-অ্যাডমিন হওয়ার সাথে সাথে সাকসেস মেসেজ লজিক ----
@dp.my_chat_member_handler()
async def bot_admin_check(update: types.ChatMemberUpdated):
    # বোট গ্রুপে অ্যাডমিন হিসেবে যুক্ত হলে বা ওল্ড স্ট্যাটাস মেম্বার থেকে অ্যাডমিন হলে
    if update.new_chat_member.status == 'administrator':
        chat_id = update.chat.id
        keyboard = InlineKeyboardMarkup(row_width=1)
        for ch in OFFICIAL_CHANNELS:
            keyboard.add(InlineKeyboardButton(text=ch["title"], url=ch["link"]))
        
        success_text = (
            f"🎉 ** can't believe it! বোটটি সফলভাবে অ্যাডমিন হিসেবে যুক্ত হয়েছে।** 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ **গ্রুপের নাম:** {update.chat.title}\n"
            f"⚙️ **স্ট্যাটাস:** `SUCCESSFUL / ACTIVE` ✅\n\n"
            f"এখন থেকে এই গ্রুপের সমস্ত সিকিউরিটি (লিংক কিলার, পাবলিক ফরওয়ার্ড প্রোটেকশন, এবং স্মার্ট কপি-পেস্ট অ্যান্টি-ব্যান) পুরোদমে সচল করা হলো!"
        )
        try:
            await bot.send_message(chat_id=chat_id, text=success_text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            print(f"সাকসেস মেসেজ পাঠাতে সমস্যা: {e}")

# ---- 🎛️ ১. অ্যাডমিন প্যানেল কমান্ড (/admin) ----
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
      
# ---- ল্যাঙ্গুয়েজ সিলেকশন ও চ্যানেল শো করার লজিক (আপডেট করা) ----
@dp.callback_query_handler(lambda call: call.data.startswith("set_lang_"))
async def set_language(call: types.CallbackQuery):
    lang = call.data.split("_")[2]
    cursor.execute("INSERT OR REPLACE INTO user_lang VALUES (?, ?)", (call.from_user.id, lang))
    conn.commit()
    
    # ইনলাইন বাটন তৈরি
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # চ্যানেল বাটনগুলো যোগ করা
    for ch in OFFICIAL_CHANNELS:
        keyboard.add(InlineKeyboardButton(text=ch["title"], url=ch["link"]))
    
    # ভেরিফাই বাটন যোগ করা
    verify_btn = InlineKeyboardButton(text=LANG_TEXT[lang]['verify'], callback_data="verify_user")
    keyboard.add(verify_btn)
    
    # মেসেজ এডিট করা (নিরাপত্তার জন্য try-except)
    try:
        await call.message.edit_text(text=LANG_TEXT[lang]['channels'], reply_markup=keyboard)
    except Exception as e:
        print(f"Error updating message: {e}")

# ---- ভেরিফিকেশন ও গ্রুপে অ্যাড করার লজিক (আপডেট করা) ----
async def verify_user_callback(call: types.CallbackQuery):
    not_joined = await check_user_joined(call.from_user.id)
    
    if not_joined:
        await call.answer("⚠️ দয়া করে সব চ্যানেলে জয়েন করুন!", show_alert=True)
    else:
        bot_user = await bot.get_me()
        
        # গ্রুপে অ্যাডমিন করার লিংক
        add_to_group_url = f"https://t.me/{bot_user.username}?startgroup=true&admin=change_info+delete_messages+restrict_members+invite_users+pin_messages+manage_video_chats"
        
        # সাকসেস বাটন
        success_keyboard = InlineKeyboardMarkup()
        success_keyboard.add(InlineKeyboardButton(text="➕ বোটটি সরাসরি আপনার গ্রুপে অ্যাডমিন করুন", url=add_to_group_url))
        
        # ফাইনাল মেসেজ এডিট করা
        try:
            await call.message.edit_text(
                text="✅ ভেরিফিকেশন সফল হয়েছে!\n\nএখন নিচের বাটনটি ক্লিক করে বোটটি আপনার গ্রুপে যুক্ত করুন। এটি স্বয়ংক্রিয়ভাবে সব পারমিশন নিয়ে অ্যাডমিন হয়ে যাবে।", 
                reply_markup=success_keyboard
            )
        except Exception as e:
            print(f"Error updating success message: {e}")

    await message.reply(
        f"👑 **স্বাগতম, মেইন অ্যাডমিন ইমরান!**\n\n"
        f"📱 বোটের বর্তমান ইউজার সংখ্যা: `{total_users}` জন\n"
        f"নিচের বাটনগুলো ব্যবহার করে বোট কন্ট্রোল করুন।",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )

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

# ---- ২. স্টার্ট কমান্ড (ইউজারদের জন্য সুন্দর কাজের বিবরণসহ) ----
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
    
    add_to_group_url = f"https://t.me/{bot_user.username}?startgroup=true&admin=change_info+delete_messages+restrict_members+invite_users+pin_messages+manage_video_chats"
    keyboard.add(InlineKeyboardButton(text="➕ বোটটি সরাসরি আপনার গ্রুপে অ্যাডমিন করুন", url=add_to_group_url))

    welcome_text = (
        f"👋 **হ্যালো {message.from_user.first_name}!**\n\n"
        f"🛡️ এটি একটি অত্যন্ত উন্নত **টেলিগ্রাম গ্রুপ সিকিউরিটি বোট**। এটি আপনার গ্রুপকে স্প্যামার এবং চোরদের হাত থেকে ১০০% সুরক্ষিত রাখবে।\n\n"
        f"🤖 **এই বোটটি কী কী করতে পারে?**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚫 **কপি-পেস্ট অ্যান্টি-ব্যান:** অন্য কারও টেক্সট হুবহু কপি করে গ্রুপে পেস্ট করলেই স্প্যামার সরাসরি ব্যান হবে! (তবে হাই, হ্যালো এর মতো ছোট শব্দ সুরক্ষিত)।\n"
        f"🔗 **লিংক ও ইউজারনেম কিলার:** গ্রুপে কোনো প্রকার লিংক (`http`, `t.me`) বা `@username` শেয়ার করা মাত্রই অটো-ডিলিট হবে।\n"
        f"🔄 **স্মার্ট ফরওয়ার্ড ব্লক:** যেকোনো পাবলিক চ্যানেল থেকে পোস্ট ফরওয়ার্ড করলে ডিলিট হবে (প্রাইভেট মেসেজ ফরওয়ার্ড সেফ থাকবে)।\n"
        f"📢 **ফোর্স জয়েন লক:** অফিশিয়াল চ্যানেলে জয়েন না করে গ্রুপে কেউ মেসেজ দিতে পারবে না।\n\n"
        f"⚙️ **বোটটি চালু করার নিয়ম (Setup Guide):**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"১. প্রথমে নিচে দেওয়া আমাদের অফিশিয়াল চ্যানেলগুলোতে জয়েন করুন।\n"
        f"২. জয়েন শেষে **'✅ জয়েন করেছি (Verify)'** বাটনে ক্লিক করুন।\n"
        f"৩. এরপর **'➕ বোটটি সরাসরি আপনার গ্রুপে অ্যাডমিন করুন'** বাটনে ক্লিক করে গ্রুপে নিয়ে যান। বোটটি সরাসরি স্বয়ংক্রিয়ভাবে ফুল অ্যাডমিন হিসেবে যুক্ত হবে।\n\n"
        f"⚠️ *চ্যানেলগুলোতে জয়েন না করলে ভেরিফিকেশন সফল হবে না।*"
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
        add_to_group_url = f"https://t.me/{bot_user.username}?startgroup=true&admin=change_info+delete_messages+restrict_members+invite_users+pin_messages+manage_video_chats"
        success_keyboard.add(InlineKeyboardButton(text="➕ বোটটি এখনই আপনার গ্রুপে অ্যাডমিন করুন", url=add_to_group_url))
        
        await call.message.edit_text(
            "🎉 **অভিনন্দন! আপনার ভেরিফিকেশন সফল হয়েছে।**\n\n"
            "এই সিকিউরিটি বোটটি এখন আপনার নিজের গ্রুপের জন্য প্রস্তুত।\n"
            "নিচে দেওয়া ইনলাইন বাটনে ক্লিক করে বোটটি এখনই আপনার গ্রুপে অটো-অ্যাডমিন হিসেবে অ্যাড করে নিন!\n\n"
            "*(নোট: বোটটি গ্রুপে অ্যাড করার সাথে সাথেই স্বয়ংক্রিয়ভাবে ফুল অ্যাডমিন পারমিশন পেয়ে যাবে।)*",
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

    if message.text and (message.text.startswith('/') or message.from_user.is_bot):
        return

    if await is_admin(message.chat.id, message.from_user.id):
        if message.text and len(message.text.strip()) > 4:
            cursor.execute("INSERT OR IGNORE INTO msg_history VALUES (?)", (get_hash(message.text),))
            conn.commit()
        return

    # ১. ফোর্স জয়েন চেক
    not_joined = await check_user_joined(message.from_user.id)
    if not_joined:
        try:
            await message.delete()
            keyboard = InlineKeyboardMarkup(row_width=1)
            for ch in not_joined:
                keyboard.add(InlineKeyboardButton(text=ch["title"], url=ch["link"]))
            
            await message.answer(
                f"⚠️ @{message.from_user.username}, আপনি আমাদের অফিশিয়াল চ্যানেলগুলোতে জয়েন করেননি!\n"
                f"গ্রুপে মেসেজ দেওয়ার অধিকার পেতে নিচের চ্যানেলগুলোতে জয়েন করুন।", 
                reply_markup=keyboard
            )
        except Exception:
            pass
        return

    # ২. স্মার্ট ফরওয়ার্ড ফিল্টার
    if message.forward_from_chat:
        if message.forward_from_chat.username:
            try:
                await message.delete()
                await message.answer(f"❌ @{message.from_user.username}, পাবলিক চ্যানেল বা গ্রুপ থেকে পোস্ট ফরওয়ার্ড করা নিষেধ!")
                return
            except Exception:
                pass
    elif message.forward_from:
        pass

    # ৩. লিংক ও ইউজারনেম ফিল্টার
    if message.text:
        if "t.me/" in message.text or "http" in message.text or "@" in message.text:
            try:
                await message.delete()
                await message.answer(f"❌ @{message.from_user.username}, গ্রুপে কোনো লিংক বা ইউজারনেম শেয়ার করা সম্পূর্ণ নিষেধ!")
                return
            except Exception:
                pass

        # ৪. কপি-পেস্ট ফিল্টার
        clean_text = message.text.strip()
        if len(clean_text) <= 4:
            return

        text_hash = get_hash(clean_text)
        cursor.execute("SELECT hash FROM msg_history WHERE hash=?", (text_hash,))
        
        if cursor.fetchone():
            try:
                await message.delete()
                await bot.kick_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
                
                warning_text = (
                    f"🚨 **কপি-পেস্ট নোটিশ ও ব্যান নোটিশ!** 🚨\n\n"
                    f"👤 **ইউজার:** @{message.from_user.username}\n"
                    f"🆔 **আইডি:** `{message.from_user.id}`\n\n"
                    f"❌ **অপরাধ:** এই গ্রুপে থাকা অন্য কোনো ইউজারের আসল পোস্ট হুবহু কপি করে পেস্ট করার চেষ্টা করা হয়েছে।\n\n"
                    f"📢 **অ্যাকশন:** গ্রুপের নিয়ম ভঙ্গ করায় ইউজারকে গ্রুপ থেকে **ব্যান (Ban)** করা হলো!"
                )
                await message.answer(warning_text, parse_mode="Markdown")
            except Exception as e:
                print(f"ব্যান করতে সমস্যা: {e}")
        else:
            cursor.execute("INSERT OR IGNORE INTO msg_history VALUES (?)", (text_hash,))
            conn.commit()

if __name__ == '__main__':
    # 🎯 মেইন ফিক্স: বোট যেন সব ধরনের চ্যাট মেম্বার আপডেট ব্যাকগ্রাউন্ডে চেক করতে পারে তা নিশ্চিত করা হলো
    executor.start_polling(dp, skip_updates=True, allowed_updates=types.AllowedUpdates.all())
