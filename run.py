import requests
from bs4 import BeautifulSoup
import pandas as pd
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import time

TOKEN = '7782698870:AAHWqsRJYuISGiSDzktRQTcf3ThC17xyry4'
bot = Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

subscribers = set()  # A set to store subscribed users

def start(update: Update, context: CallbackContext):
    subscribers.add(update.message.chat_id)
    update.message.reply_text('You have subscribed to the latest offers!')

def stop(update: Update, context: CallbackContext):
    subscribers.discard(update.message.chat_id)
    update.message.reply_text('You have unsubscribed from the latest offers.')

def fetch_latest_offers(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    if response.status_code != 200:
        return [], None

    soup = BeautifulSoup(response.content, 'html.parser')
    offers = []
    for offer in soup.select('.last_activity'):
        title = offer.select_one('h5 a').text.strip()
        link = offer.select_one('h5 a')['href']
        full_link = f"https://khamsat.com{link}"
        if "requests" in link:
            offers.append({'Title': title, 'Link': full_link})
    next_url = offers[0]['Link'] if offers else None
    return offers, next_url

def send_offers_to_subscribers(offers):
    message = '\n'.join([f"{offer['Title']}: {offer['Link']}" for offer in offers])
    for chat_id in subscribers:
        bot.send_message(chat_id=chat_id, text=message)

def main_loop():
    url = 'https://khamsat.com/community/requests/727126'
    while True:
        offers, new_url = fetch_latest_offers(url)
        if offers:
            send_offers_to_subscribers(offers)
            url = new_url  # Update the URL with the top offer's URL
        time.sleep(60)

start_handler = CommandHandler('start', start)
stop_handler = CommandHandler('stop', stop)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(stop_handler)

updater.start_polling()  # Start the bot
main_loop()  # Start the fetching loop
