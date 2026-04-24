TOKEN = "8708315455:AAFtMZ850ApwugkvjmyuVKdQVIc8bUriKSY"  # ⚠️ BotFather token
import telebot
import sqlite3
from telebot.types import *

ADMIN_ID = 8440344034

# 👇 KANAL
CHANNELS = ["@Fazliddin_Nizomiddinovf", "@oq_qorafonli_rasmlar_011_012"]

bot = telebot.TeleBot(TOKEN)

# ================= DATABASE =================
conn = sqlite3.connect("users.db", check_same_thread=False)

def get_cursor():
    return conn.cursor()

cur = get_cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT,
    balance INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    file_id TEXT,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()

# ================= OBUNA =================
def check_sub(user_id):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_keyboard():
    kb = InlineKeyboardMarkup()
    for ch in CHANNELS:
        kb.add(InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.replace('@','')}"))
    kb.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
    return kb

# ================= USER =================
def add_user(user):
    cur = get_cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users (user_id, name, username) VALUES (?, ?, ?)",
            (user.id, user.first_name, user.username)
        )
        conn.commit()
        bot.send_message(ADMIN_ID, f"🆕 Yangi user: {user.id}")

# ================= MENU =================
def menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💳 To‘lov qilish", "💼 Hisobim")
    kb.add("🗂 Xizmatlar", "📞 Yordam")
    return kb

# ================= START =================
@bot.message_handler(commands=['start'])
def start(m):
    add_user(m.from_user)

    if not check_sub(m.from_user.id):
        bot.send_message(
            m.chat.id,
            "⛔ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:",
            reply_markup=sub_keyboard()
        )
        return

    bot.send_message(
        m.chat.id,
        f"👋 Salom, {m.from_user.first_name}!",
        reply_markup=menu()
    )
# ================= MAIN =================
@bot.message_handler(func=lambda m: True)
def handler(m):

    if not check_sub(m.from_user.id):
        bot.send_message(
            m.chat.id,
            "❗ Avval kanalga obuna bo‘ling:",
            reply_markup=ReplyKeyboardRemove()
        )
        bot.send_message(m.chat.id, "👇 Obuna bo‘ling:", reply_markup=sub_keyboard())
        return

    text = m.text

    # BALANS
    if text == "💼 Hisobim":
        cur = get_cursor()
        cur.execute("SELECT balance FROM users WHERE user_id=?", (m.from_user.id,))
        bal = cur.fetchone()[0]
        bot.send_message(m.chat.id, f"💰 Balans: {bal:,} so‘m")

    # PAYMENT
    elif text == "💳 To‘lov qilish":
        bot.send_message(m.chat.id, "💵 Summani yozing:")
        bot.register_next_step_handler(m, get_amount)

    # SERVICES
    elif text == "🗂 Xizmatlar":

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(
            InlineKeyboardButton("📸 Instagram", callback_data="insta"),
            InlineKeyboardButton("💬 Telegram", callback_data="tg")
        )

        kb.add(
            InlineKeyboardButton("📷 YouTube", callback_data="yt"),
            InlineKeyboardButton("📽 TikTok", callback_data="tt")
        )


        

        kb.add(
            InlineKeyboardButton("🎁 Tekin Xizmatlar", callback_data="free")
        )

        kb.add(
            InlineKeyboardButton("⭐️ Telegram Premium", callback_data="premium")
        )
        bot.send_message(
    m.chat.id,
    "⭐ <b>Bizning xizmatlarni tanlaganingizdan mamnunmiz!</b>\n\n <b>👇 Quyidagi ijtimoiy tarmoqlardan birini tanlang.</b>",
    reply_markup=kb,
    parse_mode="HTML"
)

    # HELP
    elif text == "📞 Yordam":
        bot.send_message(m.chat.id, "📩 Admin: @Fazliddin_iq")

# ================= AMOUNT =================
def get_amount(m):

    if not check_sub(m.from_user.id):
        bot.send_message(m.chat.id, "❗ Obuna bo‘ling:", reply_markup=ReplyKeyboardRemove())
        bot.send_message(m.chat.id, "👇 Kanal:", reply_markup=sub_keyboard())
        return

    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Faqat raqam kiriting:")
        bot.register_next_step_handler(m, get_amount)
        return

    amount = int(m.text)

    bot.send_message(m.chat.id, "📸 Chek yuboring (rasm)")
    bot.register_next_step_handler(m, lambda msg: get_receipt(msg, amount))

# ================= RECEIPT =================
def get_receipt(m, amount):

    if not check_sub(m.from_user.id):
        bot.send_message(m.chat.id, "❗ Obuna bo‘ling:", reply_markup=ReplyKeyboardRemove())
        bot.send_message(m.chat.id, "👇 Kanal:", reply_markup=sub_keyboard())
        return

    if not m.photo:
        bot.send_message(m.chat.id, "❌ Rasm yuboring!")
        bot.register_next_step_handler(m, lambda msg: get_receipt(msg, amount))
        return

    file_id = m.photo[-1].file_id
    cur = get_cursor()

    cur.execute(
        "INSERT INTO payments (user_id, amount, file_id, status) VALUES (?, ?, ?, 'pending')",
        (m.from_user.id, amount, file_id)
    )
    conn.commit()

    pay_id = cur.lastrowid

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅", callback_data=f"ok_{pay_id}"),
        InlineKeyboardButton("❌", callback_data=f"no_{pay_id}")
    )

    bot.send_photo(
        ADMIN_ID,
        file_id,
        caption=f"🧾 CHEK\nID:{pay_id}\nUser:{m.from_user.id}\nSumma:{amount}",
        reply_markup=kb
    )

    bot.send_message(m.chat.id, "⏳ Tekshirilmoqda...")

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def call(c):

    # CHECK SUB
    if c.data == "check_sub":
        if check_sub(c.from_user.id):
            bot.delete_message(c.message.chat.id, c.message.message_id)
            bot.send_message(c.message.chat.id, "✅ Obuna tasdiqlandi!", reply_markup=menu())
        else:
            bot.answer_callback_query(c.id, "❌ Obuna yo‘q")
        return

    # ================= INSTAGRAM =================
    elif c.data == "insta":

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(
            InlineKeyboardButton("👥 Obunachi", callback_data="insta_sub")
        )

        kb.add(
            InlineKeyboardButton("👀 Prosmotr", callback_data="insta_view")
        )

        kb.add(
            InlineKeyboardButton("❤️ Like", callback_data="insta_like")
        )

        kb.add(
            InlineKeyboardButton("⬅️ Orqaga", callback_data="back_services")
        )

        bot.edit_message_text(
            "📸 Instagram bo‘limiga xush kelibsiz!\n 📋 Kerakli xizmat turini tanlang:",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=kb
        )
        return

    # ================= TELEGRAM =================
    elif c.data == "tg":

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(
            InlineKeyboardButton("👥 Obunachi", callback_data="tg_sub")
        )

        kb.add(
            InlineKeyboardButton("👀 Prosmotr", callback_data="tg_view")
        )

        kb.add(
            InlineKeyboardButton("", callback_data="tg_view")
        )

        kb.add(
            InlineKeyboardButton("⬅️ Orqaga", callback_data="back_services")
        )



        bot.edit_message_text(
    "💬 <b>Telegram bo‘limiga xush kelibsiz!</b>\n\n📋 Kerakli xizmat turini tanlang:",
    c.message.chat.id,
    c.message.message_id,
    reply_markup=kb,
    parse_mode="HTML"
)
        return

    # ================= ACTIONS =================
    elif c.data in ["insta_sub", "insta_view", "insta_like",
                    "tg_sub", "tg_view", "tg_like"]:
        bot.answer_callback_query(c.id, "✅ Xizmat tanlandi")
# ================= RUN =================
print("🚀 BOT ISHLAYAPTI")

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("Xatolik:", e)