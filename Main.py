import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Constants
STEAM_URL = "https://store.steampowered.com/app/227300/Euro_Truck_Simulator_2/"
TARGET_PRICE = 5.00  # Target price in USD
CHECK_INTERVAL = 3600  # Check every hour (3600 seconds)

# Open Exchange Rates API
OPEN_EXCHANGE_URL = "https://openexchangerates.org/api/latest.json"
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

# List of recommended games (just as an example)
RECOMMENDED_GAMES = [
    {"name": "American Truck Simulator", "url": "https://store.steampowered.com/app/270880/American_Truck_Simulator/"},
    {"name": "Farming Simulator 19", "url": "https://store.steampowered.com/app/836930/Farming_Simulator_19/"},
    {"name": "Cities: Skylines", "url": "https://store.steampowered.com/app/255710/Cities_Skylines/"}
]

def get_exchange_rates():
    """Fetch exchange rates from Open Exchange Rates API."""
    try:
        response = requests.get(OPEN_EXCHANGE_URL, params={"app_id": EXCHANGE_API_KEY})
        response.raise_for_status()
        data = response.json()
        return data["rates"]
    except Exception as e:
        raise ValueError(f"Failed to fetch exchange rates: {e}")

def convert_to_usd(price, currency, exchange_rates):
    """Convert a price from a given currency to USD."""
    if currency not in exchange_rates:
        raise ValueError(f"Currency {currency} not supported in exchange rates.")
    return price / exchange_rates[currency]

def get_game_price():
    """Fetch the current price of the game."""
    response = requests.get(STEAM_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for the price element
    price_element = soup.find("div", class_="game_purchase_price price")  # Update with correct class
    if not price_element:
        raise ValueError("Could not find price element on the page")
    
    # Extract and clean the price text
    price_text = price_element.text.strip()
    currency = "USD"  # Default currency (update if necessary)
    
    # Detect currency
    if "₹" in price_text:
        currency = "INR"
    elif "$" in price_text:
        currency = "USD"
    elif "€" in price_text:
        currency = "EUR"
    
    # Remove non-numeric characters except dots
    price_text = ''.join(char for char in price_text if char.isdigit() or char == '.')
    return float(price_text), currency

def send_email_notification(price, recommendations):
    """Send an email notification with the price and recommendations."""
    subject = "Price Alert: Euro Truck Simulator 2 is now ${:.2f}".format(price)
    body = f"The game is now available for ${price} on Steam. Check it out here: {STEAM_URL}\n\nRecommended games for you:\n"
    
    for game in recommendations:
        body += f"{game['name']} - {game['url']}\n"
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = TO_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, TO_EMAIL, msg.as_string())
    print(f"Notification sent to {TO_EMAIL}")

def main():
    try:
        exchange_rates = get_exchange_rates()  # Fetch exchange rates
    except ValueError as e:
        print(f"Error fetching exchange rates: {e}")
        return
    
    while True:
        try:
            current_price, currency = get_game_price()
            print(f"Current price: {current_price} {currency}")
            
            if currency != "USD":
                current_price = convert_to_usd(current_price, currency, exchange_rates)
                print(f"Converted price: ${current_price:.2f} USD")
            
            if current_price <= TARGET_PRICE:
                send_email_notification(current_price, RECOMMENDED_GAMES)
                break  # Stop the script after notification
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
