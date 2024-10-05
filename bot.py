import asyncio
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
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
subscribers = set()
last_offer_sent = None  # Stores the last offer sent to avoid duplicates

def fetch_latest_offers(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        offers = []
        # Selecting only the <h5> tags within .last_activity which contain the <a> tags with the project info
        project_links = soup.select('.last_activity .o-media__body h5 a')
        for link in project_links:
            title = link.text.strip()
            href = 'https://khamsat.com' + link['href']  # Prepend the base URL to make the link absolute
            offers.append({'title': title, 'link': href})
        logger.info(f"Fetched {len(offers)} offers.")
        return offers
    else:
        logger.error(f"Failed to fetch offers with status code {response.status_code}.")
    return []


async def send_offers_periodically():
    global last_offer_sent
    while True:
        logger.info("Checking for new offers...")
        if not subscribers:
            logger.info("No subscribers to send offers to.")
        else:
            url = 'https://khamsat.com/community/requests/727126'
            offers = fetch_latest_offers(url)
            if offers:
                latest_offer = offers[0]
                if latest_offer != last_offer_sent:
                    last_offer_sent = latest_offer
                    message = f"{latest_offer['title']} \n <a href='{latest_offer['link']}'>اضغط هنا لمزيد من التفاصيل</a>"
                    logger.info(f"Preparing to send latest offer to {len(subscribers)} subscribers.")
                    for chat_id in subscribers:
                        try:
                            await application.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
                            logger.info(f"Sent latest offer to {chat_id}.")
                        except Exception as e:
                            logger.error(f"Failed to send message to {chat_id}: {str(e)}")
                else:
                    logger.info("No new offers to send since the last check.")
            else:
                logger.info("No offers found.")
        await asyncio.sleep(10)  # Waits for 1 hour

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.add(update.effective_chat.id)
    await update.message.reply_text('مُبارك .. أهلاً وسهلاً بالمليونير الجديد!')
    logger.info(f"Added subscriber: {update.effective_chat.id}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in subscribers:
        subscribers.remove(update.effective_chat.id)
        await update.message.reply_text('خسارة لَنا :(')
        logger.info(f"Removed subscriber: {update.effective_chat.id}")
    else:
        await update.message.reply_text('You were not subscribed.')

def run():
    global application
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    loop = asyncio.get_event_loop()
    loop.create_task(send_offers_periodically())
    application.run_polling()

if __name__ == '__main__':
    run()
