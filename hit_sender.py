import requests
import random

def escape_html(s):
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))

def send(cc, last, username, time_taken, remaining):
    ii = (cc or "")[:6]
    cents = random.randint(50, 99)

    bank = "Unknown"
    country = "Unknown"
    emj = "🏳️"

    # BIN lookup
    try:
        r = requests.get(f"https://bins.antipublic.cc/bins/{ii}", timeout=10)
        r.raise_for_status()
        data = r.json()
        bank = data.get("bank", bank)
        country = data.get("country", country)
        emj = data.get("country_flag", emj)
    except Exception as e:
        print("BIN API ERROR:", e)

    # RESULT ICON
    u = (last or "").upper()

    if "CHARG" in u:   # CHARGED / 𝐂𝐡𝐚𝐫𝐠𝐞𝐝
        icon = "🟢"
    elif any(x in u for x in ("DECLINED", "DEAD", "INSUFFICIENT")):
        icon = "🔴"
    else:
        icon = "🟡"

    # Escape output
    cc_e = escape_html(cc)
    last_e = escape_html(last)
    bank_e = escape_html(bank)
    country_e = escape_html(country)
    user_e = escape_html(username or "NoUsername")
    taken_e = escape_html(time_taken)
    rem_e = escape_html(remaining)

    # FINAL MESSAGE (PREMIUM 👑 STYLE)
    msg = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{icon} <b>RESULT</b> : <b>{last_e}</b>\n"
        f"💸 <b>AMOUNT</b> : <code>0.{cents:02d}$</code>\n"
        f"⏱ <b>TIME</b> : <code>{taken_e}s</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💳 <b>CARD</b>\n"
        f"<code>{cc_e}</code>\n\n"
        "🏦 <b>BIN INFO</b>\n"
        f"• <b>Bank</b> : {bank_e}\n"
        f"• <b>Country</b> : {country_e} {emj}\n"
        f"• <b>BIN</b> : <code>{escape_html(ii)}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 @{user_e} 👑 <b>PREMIUM</b>\n"
        f"💳 <b>Credits</b> : <code>{rem_e}</code>\n"
        "🤖 <b>@buik100</b>"
    )

    return msg