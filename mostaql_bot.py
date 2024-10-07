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
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TOKEN = '8166315425:AAFROfao50LcrOm2qPBP05Q9qhreEoh23Fg'
CHANNEL_ID = '-1002282544683'
last_offer_sent = None
url = 'https://mostaql.com/projects'  # URL to fetch from Mostaql

def fetch_latest_offers():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        first_link = soup.select_one("body > div.wrapper.hsoub-container > div > div.page-body > div > div.row > div.col-md-9.collection-browse--panel > div > table > tbody > tr:nth-child(1) > td > div.card-title_wrapper > div.card--title > h2 > a")
        if first_link and 'href' in first_link.attrs:
            link = first_link['href'].strip()
            # Check if the link is relative and prepend the base URL if necessary
            if link.startswith('/'):
                link = 'https://mostaql.com' + link
            return [{'link': link}]
    else:
        logger.error(f"Failed to fetch offers with status code {response.status_code}")
    return []

def fetch_offer_details(offer_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(offer_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.select_one("body > div.wrapper.hsoub-container > div > div.page-body > div > div.page-title > div:nth-child(2) > div > h1 > span").text.strip()
        description = soup.select_one("#project-brief-panel > div")
        budget = soup.select_one("#project-meta-panel > div:nth-child(1) > table > tbody > tr:nth-child(3) > td:nth-child(2) > span")
        deadline = soup.select_one("#project-meta-panel > div:nth-child(1) > table > tbody > tr:nth-child(4) > td:nth-child(2)")

        description_text = description.text.strip() if description else "No description available"
        budget_text = budget.text.strip() if budget else "No budget specified"
        deadline_text = deadline.text.strip() if deadline else "No deadline specified"

        return title, description_text, budget_text, deadline_text
    else:
        logger.error(f"Failed to fetch details from {offer_url} with status code {response.status_code}")
        return None, None, None, None


async def send_offers_to_channel(application):
    global last_offer_sent
    while True:
        logger.info("Checking for new offers...")
        offers = fetch_latest_offers()
        if offers:
            latest_offer = offers[0]
            if latest_offer != last_offer_sent:
                last_offer_sent = latest_offer
                title, description, budget, deadline = fetch_offer_details(latest_offer['link'])
                if title and description:
                    message = f"<b>📌 {title}</b>\n\n{description}\n\nالميزانية 💵 {budget}\n\nمدة التنفيذ 🕛 {deadline} \n\n<a href='{latest_offer['link']}'>اذهب إلى العرض 🔗</a>"
                    
                    try:
                        await application.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='HTML', disable_web_page_preview=True)
                        logger.info("Sent latest offer to the channel.")
                    except Exception as e:
                        logger.error(f"Failed to send message to the channel: {str(e)}")
            else:
                logger.info("No new offers to send since the last check.")
        else:
            logger.info("No offers found.")
        await asyncio.sleep(15)  # Adjust the frequency of checks as needed

def main():
    application = Application.builder().token(TOKEN).build()
    loop = asyncio.get_event_loop()
    loop.create_task(send_offers_to_channel(application))
    application.run_polling()

if __name__ == '__main__':
    main()
