import os
import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PRODUCTS_TO_TRACK = [
    {
        "store": "Torédo",
        "url": "https://www.toredo.cz/pokemon-booster-box-example/",
        "selector": "button.add-to-cart" # Replace with actual Torédo button selector
    },
    {
        "store": "Najada",
        "url": "https://www.najada.cz/cz/pokemon-booster-box-example/",
        "selector": "#btn-buy" # Replace with actual Najada button selector
    }
]


def send_telegram_alert(message):
    """Sends a push notification via Telegram Bot API."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not found.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
        print("Alert sent to Telegram!")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")


def check_all_stock():
    """Loops through all stores and checks stock."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        for product in PRODUCTS_TO_TRACK:
            print(f"Checking {product['store']}...")
            try:
                page.goto(product['url'], timeout=30000)
                page.wait_for_selector(product['selector'], state="visible", timeout=5000)

                print(f"🚨 {product['store']} IS IN STOCK!")
                send_telegram_alert(f"🚨 <b>{product['store']} IN STOCK</b> 🚨\n<a href='{product['url']}'>Buy Here</a>")

            except TimeoutError:
                print(f"{product['store']}: Out of stock (Buy button not found).")
            except Exception as e:
                print(f"{product['store']} Page error: {e}")

            # Pause for 3 seconds between websites so we don't get blocked
            time.sleep(3)

        browser.close()


def main():
    print("Starting TCG Restock Tracker...")
    check_all_stock()


if __name__ == "__main__":
    main()