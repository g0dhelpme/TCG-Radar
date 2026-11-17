import os
import time
import requests
import json
from playwright.sync_api import sync_playwright, TimeoutError

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "prices.json" #  file for prices comparison
PRODUCTS_TO_TRACK = [
    {
        "store": " - ETB",
        "url": "https://www.digihry.sk/p-69636/pokemon-tcg-30th-celebration-elite-trainer-box-tcg",
        "button_selector": "#kosik_add_button",
        "price_selector":"#main_price"
    },
    {
        "store": "DIGIHRY - Bundle",
        "url": "https://www.digihry.sk/p-69630/pokemon-tcg-30th-celebration-booster-bundle-tcg",
        "button_selector": "#kosik_add_button",
        "price_selector":"#main_price"
    },
    {
        "store": "Najada - Bundle",
        "url": "https://www.najada.games/produkt/30th-celebration-booster-bundle-B6A4GP",
        "button_selector": "div.Button.basket",
        "price_selector":".mainPrice .value"
    },
    {
        "store": "Najada - ETB",
        "url": "https://www.najada.games/produkt/30th-celebration-elite-trainer-box-DJ8BID",
        "button_selector": "div.Button.basket",
        "price_selector":".mainPrice .value"
    },
    {
        "store": "Sparkys - Bundle",
        "url": "https://www.sparkys.cz/pokemon-tcg-30th-celebration-booster-bundle/",
        "button_selector": "button.rf-Button--buy",
        "price_selector":".Product-priceFinal .rf-Price-content"
    },
    {
        "store": "Sparkys - ETB",
        "url": "https://www.sparkys.cz/pokemon-tcg-30th-celebration-elite-trainer-box/",
        "button_selector": "button.rf-Button--buy",
        "price_selector":".Product-priceFinal .rf-Price-content"
    },
]

def load_previous_prices():
    """Loads the saved prices from the last run."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_current_prices(prices_dict):
    """Saves the current prices to be read during the next run."""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(prices_dict, f, indent=4)

def send_telegram_alert(message):
    """Sends a push notification via Telegram Bot API."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not found in environment variables.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)

        # Check if Telegram actually accepted the message
        if response.status_code == 200:
            print("Alert successfully delivered to Telegram!")
        else:
            # If Telegram rejected it, print the exact reason why
            print(f"Telegram rejected the message! Error: {response.text}")

    except Exception as e:
        print(f"Network error while contacting Telegram: {e}")

def check_all_stock():
    previous_prices = load_previous_prices()
    current_prices = previous_prices.copy()  # We will update this and save it later

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        })

        for product in PRODUCTS_TO_TRACK:
            store_name = product['store']
            print(f"Checking {store_name}...")

            try:
                page.goto(product['url'], timeout=30000)

                # First, try to read the current price
                page.wait_for_selector(product['price_selector'], timeout=5000)
                current_price_text = page.locator(product['price_selector']).inner_text().strip()

                # Check if the buy button is visible
                try:
                    page.wait_for_selector(product['button_selector'], state="visible", timeout=5000)
                    is_in_stock = True
                except TimeoutError:
                    is_in_stock = False

                if is_in_stock:
                    last_price = previous_prices.get(store_name)

                    # Scenario 1: Price has changed!
                    if last_price and last_price != current_price_text:
                        print(f"🚨 {store_name} Price Changed: {last_price} -> {current_price_text}")
                        send_telegram_alert(
                            f"📉 <b>PRICE CHANGE AT {store_name}</b> 📈\n\n"
                            f"Old Price: <s>{last_price}</s>\n"
                            f"New Price: <b>{current_price_text}</b>\n\n"
                            f"<a href='{product['url']}'>Buy Here</a>"
                        )

                    # Scenario 2: It wasn't tracked before (or just came in stock), alert normal restock
                    elif not last_price:
                        print(f"🚨 {store_name} IN STOCK! Price: {current_price_text}")
                        send_telegram_alert(
                            f"🚨 <b>{store_name} IN STOCK</b> 🚨\n\n"
                            f"Price: <b>{current_price_text}</b>\n"
                            f"<a href='{product['url']}'>Buy Here</a>"
                        )

                    # Update our dictionary with the new price
                    current_prices[store_name] = current_price_text

                else:
                    print(f"{store_name}: Out of stock.")
                    # If out of stock, remove it from memory so it alerts freshly next time it restocks
                    if store_name in current_prices:
                        del current_prices[store_name]

            except Exception as e:
                print(f"{store_name} Page error: {e}")

            time.sleep(3)

        browser.close()

    # Save the new prices to the JSON file before the script ends
    save_current_prices(current_prices)


if __name__ == "__main__":
    check_all_stock()