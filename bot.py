import asyncio
import logging
from telegram.ext import Application
import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),  # Logs to a file named 'bot.log'
        logging.StreamHandler()          # And logs to the console
    ]
)
logger = logging.getLogger(__name__)

TOKEN = '7782698870:AAHWqsRJYuISGiSDzktRQTcf3ThC17xyry4'
CHANNEL_ID = '-1002365070199'
last_offer_sent = None
url = 'https://khamsat.com/community/requests/727126'

def fetch_latest_offers(current_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(current_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        offers = [{'link': 'https://khamsat.com' + link['href'], 'title': link.text.strip()}
                  for link in soup.select('.last_activity .o-media__body h5 a') if "requests" in link['href']]
        return offers
    else:
        logger.error(f"Failed to fetch offers with status code {response.status_code}")
    return []

def fetch_offer_details(offer_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(offer_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.select_one("#header-group > div.heading.col-lg-9.col-8.full_width > div > h1").text.strip()
        description = soup.select_one("body > div.hsoub-container > div > div:nth-child(2) > div > div:nth-child(3) > div.col-md-12.col-sm-12.js-page.col-lg-8 > div:nth-child(1) > div > article").text.strip()
        return title, description
    else:
        logger.error(f"Failed to fetch details from {offer_url} with status code {response.status_code}")
        return None, None

async def send_offers_to_channel(application):
    global last_offer_sent, url
    while True:
        logger.info("Checking for new offers...")
        offers = fetch_latest_offers(url)
        if offers:
            latest_offer = offers[0]
            if latest_offer != last_offer_sent:
                last_offer_sent = latest_offer
                url = latest_offer['link']  # Update the URL to the new offer link
                title, description = fetch_offer_details(latest_offer['link'])
                if title and description:
                    message = f"<b>📌 {title}</b>\n\n 📃 {description}\n\n<a href='{latest_offer['link']}'>اذهب إلى العرض 🔗</a>"
                    try:
                        await application.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='HTML', disable_web_page_preview=True)
                        logger.info("Sent latest offer to the channel.")
                    except Exception as e:
                        logger.error(f"Failed to send message to the channel: {e}")
            else:
                logger.info("No new offers to send.")
        else:
            logger.info("No offers found.")
        await asyncio.sleep(15)  # Wait for 1 hour before checking again

def main():
    application = Application.builder().token(TOKEN).build()
    loop = asyncio.get_event_loop()
    loop.create_task(send_offers_to_channel(application))
    application.run_polling()

if __name__ == '__main__':
    main()
