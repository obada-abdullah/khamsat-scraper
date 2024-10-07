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

TOKEN = '7782698870:AAHWqsRJYuISGiSDzktRQTcf3ThC17xyry4'  # Without the trailing "s"
CHANNEL_ID = '-1002365070199'  # Replace with the correct channel ID
last_offer_sent = None  # Stores the last offer sent to avoid duplicates
url = 'https://khamsat.com/community/requests/727126'  # Initial URL

# Function to fetch the latest offers containing 'requests' in their link
def fetch_latest_offers():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        offers = [{'link': 'https://khamsat.com' + link['href']}
                  for link in soup.select('.last_activity .o-media__body h5 a') if "requests" in link['href']]
        return offers
    else:
        logger.error(f"Failed to fetch offers with status code {response.status_code}")
    return []

# Function to fetch offer details (title and description) from inside the offer link
def fetch_offer_details(offer_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(offer_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract the title
        title = soup.select_one("#header-group > div.heading.col-lg-9.col-8.full_width > div > h1").text.strip()
        # Extract the description
        description = soup.select_one("body > div.hsoub-container > div > div:nth-child(2) > div > div:nth-child(3) > div.col-md-12.col-sm-12.js-page.col-lg-8 > div:nth-child(1) > div > article").text.strip()
        return title, description
    else:
        logger.error(f"Failed to fetch details from {offer_url} with status code {response.status_code}")
        return None, None

# Function to periodically send the latest offer to the channel
async def send_offers_to_channel(application):
    global last_offer_sent
    while True:
        logger.info("Checking for new offers...")
        offers = fetch_latest_offers()
        if offers:
            latest_offer = offers[0]  # Only fetch the latest offer
            if latest_offer != last_offer_sent:  # Send only if it's a new offer
                last_offer_sent = latest_offer  # Update the last sent offer

                # Fetch details of the latest offer (title and description)
                title, description = fetch_offer_details(latest_offer['link'])
                if title and description:
                    # Create the message with title, link, and description
                    message = f"<b>📌 {title}</b>\n\n 📃 {description}\n\n<a href='{latest_offer['link']}'>اذهب إلى العرض 🔗</a>"
                    try:
                        # Send the message to the channel
                        await application.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='HTML')
                        logger.info(f"Sent latest offer to the channel: {CHANNEL_ID}")
                    except Exception as e:
                        logger.error(f"Failed to send message to the channel: {str(e)}")
            else:
                logger.info("No new offers to send.")
        else:
            logger.info("No offers found.")
        await asyncio.sleep(3600)  # Wait for 1 hour before checking again

# Main function to run the bot
def main():
    application = Application.builder().token(TOKEN).build()
    loop = asyncio.get_event_loop()
    loop.create_task(send_offers_to_channel(application))  # Schedule offer sending task
    application.run_polling()

if __name__ == '__main__':
    main()
