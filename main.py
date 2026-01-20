# ===== IMPORTS =====
import os
import json
import time
import re
import requests
from telebot import TeleBot
from gatet import Tele

# ===== CONFIG =====
MAX_CARDS = 10
checker_name = "@buik100"   # 🔧 ကိုယ့် checker name

# ===== ADMINS =====
ADMIN_IDS = [
    7102484985,  # 🔧 ကိုယ့် Telegram user_id
]

# ===== LOAD TOKEN =====
with open("token.txt", "r") as f:
    TOKEN = f.read().strip()

bot = TeleBot(TOKEN, parse_mode="HTML")

# ================= LOG CHANNEL =================
LOG_CHANNEL = -1003530017927  # channel / group id

try:
    bot.send_message(LOG_CHANNEL, "✅ LOG TEST OK")
    print("LOG OK")
except Exception as e:
    print("LOG FAIL:", e)

# ================= DB =================
CREDITS_FILE = "credits.json"
DEFAULT_CREDITS = 1

def load_db():
    if not os.path.exists(CREDITS_FILE):
        return {}
    try:
        with open(CREDITS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(db):
    with open(CREDITS_FILE, "w") as f:
        json.dump(db, f, indent=2)

def ensure_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"credits": DEFAULT_CREDITS}
        save_db(db)
    return db

def spend_credit_or_block(message, cost):
    db = ensure_user(message.from_user.id)
    uid = str(message.from_user.id)

    if db[uid]["credits"] < cost:
        bot.reply_to(message, "❌ No credits left. Use /request")
        return None

    db[uid]["credits"] -= cost
    save_db(db)
    return db[uid]["credits"]

# ================= BIN LOOKUP =================
BIN_CACHE = {}

def get_bin_info(cc):
    bin6 = cc.split("|", 1)[0][:6]
    if bin6 in BIN_CACHE:
        return BIN_CACHE[bin6]

    info = {
        "bank": "UNKNOWN",
        "country": "UNKNOWN",
        "flag": "🏳️"
    }

    try:
        r = requests.get(f"https://bins.antipublic.cc/bins/{bin6}", timeout=5)
        r.raise_for_status()
        d = r.json()
        info["bank"] = d.get("bank", info["bank"])
        info["country"] = d.get("country", info["country"])
        info["flag"] = d.get("country_flag", info["flag"])
    except:
        pass

    BIN_CACHE[bin6] = info
    return info

# ================= COMMANDS =================
@bot.message_handler(commands=["start"])
def start_cmd(message):
    db = ensure_user(message.from_user.id)
    credits = db[str(message.from_user.id)]["credits"]
    username = message.from_user.username or "NoUsername"

    bot.reply_to(
        message,
        f"👤 @{username}\n"
        f"💳 Credits: {credits}\n\n"
        "› /cvv cc|mm|yy|cvv (max 10)\n"
        "› /request - Request Credits\n"
        "› /addcredits user_id amount (admin)"
    )

@bot.message_handler(commands=["request"])
def request_cmd(message):
    uid = message.from_user.id
    username = message.from_user.username or "NoUsername"

    bot.reply_to(message, "✅ Request sent to admin.")

    for admin_id in ADMIN_IDS:
        bot.send_message(
            admin_id,
            f"📩 <b>Credit Request</b>\n\n"
            f"User: @{username}\n"
            f"ID: <code>{uid}</code>",
            parse_mode="HTML"
        )

# ================= ADD CREDITS (ADMIN) =================
@bot.message_handler(commands=["addcredits"])
def addcredits_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not admin.")
        return

    parts = (message.text or "").split()
    if len(parts) != 3:
        bot.reply_to(message, "Usage:\n/addcredits user_id amount")
        return

    target_id = parts[1]
    try:
        amount = int(parts[2])
    except:
        bot.reply_to(message, "❌ amount must be number")
        return

    if amount <= 0:
        bot.reply_to(message, "❌ amount must be > 0")
        return

    db = load_db()
    if target_id not in db:
        db[target_id] = {"credits": 0}

    db[target_id]["credits"] += amount
    save_db(db)

    bot.reply_to(
        message,
        f"✅ <b>Credits Added</b>\n"
        f"User: <code>{target_id}</code>\n"
        f"Added: <code>{amount}</code>\n"
        f"Now: <code>{db[target_id]['credits']}</code>",
        parse_mode="HTML"
    )

    try:
        bot.send_message(
            int(target_id),
            f"🎉 <b>Credits Added!</b>\n"
            f"+<code>{amount}</code>\n"
            f"Balance: <code>{db[target_id]['credits']}</code>",
            parse_mode="HTML"
        )
    except:
        pass

# ================= CVV CHECK =================
@bot.message_handler(commands=["cvv"])
def cvv_handler(message):
    try:
        text = message.text or ""
        cards = re.findall(
            r"\d{15,16}[\s|:/]\d{1,2}[\s|:/]\d{2,4}[\s|:/]\d{3,4}",
            text
        )

        if not cards:
            bot.reply_to(message, "❌ <b>No valid cards found!</b>", parse_mode="HTML")
            return

        cc_list = [re.sub(r"[\s:/]+", "|", c) for c in cards[:MAX_CARDS]]
        card_count = len(cc_list)

        remaining = spend_credit_or_block(message, cost=card_count)
        if remaining is None:
            return

        header = (
            "👑 <b>VIP STRIPE GATE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"💳 <b>Cards</b> : {card_count}\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        msg = bot.reply_to(
            message,
            f"⏳ <b>Processing {card_count} cards...</b>\n🚀 <i>Please wait</i>",
            parse_mode="HTML"
        )

        results = []

        for cc in cc_list:
            start = time.time()
            bin_data = get_bin_info(cc)

            try:
                resp = str(Tele(cc)).lower()
                if "Donation Successful!" in resp or "successful" in resp:
                    status = "CHARGED 🔥"
                elif "insufficient" in resp:
                    status = "LOW FUNDS 💰"
                elif "incorrect_cvc" in resp or "security code" in resp:
                    status = "CCN LIVE 💳"
                elif "requires_action" in resp:
                    status = "3DS 🛡️"
                else:
                    status = "DECLINED ❌"
            except:
                status = "ERROR ⚠️"

            t = round(time.time() - start, 2)

            results.append(
                f"💳 <code>{cc}</code>\n"
                f"💬 <b>{status}</b>\n"
                f"🏦 <b>Bank</b> : {bin_data['bank']}\n"
                f"🌍 <b>Country</b> : {bin_data['country']} {bin_data['flag']}\n"
                f"⏱ <b>Time</b> : {t}s\n"
                f"━━━━━━━━━━━━━━"
            )

        username = message.from_user.username or "NoUsername"

        final_text = (
            header
            + "\n".join(results)
            + "\n\n"
            f"👤 @{username} 👑 <b>PREMIUM</b>\n"
            f"💳 <b>Credits</b> : <code>{remaining}</code>\n"
            f"🤖 <b>{checker_name}</b>"
        )

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=final_text,
            parse_mode="HTML"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ================= MAIN =================
if __name__ == "__main__":
    print("Bot is running...")
    while True:
        try:
            bot.polling(non_stop=True, timeout=30)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)