import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def fetch_latest_offers():
    url = 'https://khamsat.com/community/requests/727126'  # Replace with the actual URL of the latest contribution section
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'  # Ensure correct encoding

    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    offers = []

    # Adjust the selectors based on the actual HTML structure of the website
    for offer in soup.select('.last_activity'):
        title = offer.select_one('h5 a').text.strip()
        link = offer.select_one('h5 a')['href']
        full_link = f"https://khamsat.com{link}"
        if "requests" in link:
            offers.append({
                'Title': title,
                'Link': full_link,
            })

    return offers

def save_offers_to_file(offers):
    df = pd.DataFrame(offers)
    df.to_csv('offers.csv', index=False, encoding='utf-8-sig')

def main():
    while True:
        latest_offers = fetch_latest_offers()
        if latest_offers:
            df = pd.DataFrame(latest_offers)
            print(df.to_string(index=False, justify='left'))
            save_offers_to_file(latest_offers)  # Save offers to file
        else:
            print("No offers found or failed to fetch offers.")
        time.sleep(60)  # Wait for 60 seconds before fetching again

if __name__ == "__main__":
    main()
