#!/usr/bin/env python3
"""
Irish Immigration Visa Date Checker

This script monitors the Irish Immigration website for changes in the 
"Date applications received in Dublin" for "Tourism or visit a family/friend" category.
When a change is detected, it sends a Telegram notification.

Usage: python3 checker.py
Schedule with cron: 0 9 * * * /usr/bin/python3 /path/to/checker.py
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import logging
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Resolve paths relative to the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')
DATA_FILE = os.path.join(SCRIPT_DIR, 'last_date.json')
LOG_FILE = os.path.join(SCRIPT_DIR, 'checker.log')


def load_telegram_config():
    """Load Telegram bot_token and chat_id from config.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        if 'bot_token' not in config or 'chat_id' not in config:
            logging.error("config.json must contain 'bot_token' and 'chat_id'")
            return None
        return config
    except FileNotFoundError:
        logging.error("config.json not found. Copy config.json.example to config.json and fill in your credentials.")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config.json: {e}")
        return None


TELEGRAM_CONFIG = load_telegram_config()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_visa_date():
    """
    Scrape the Irish Immigration website to get the current date for
    "Tourism or visit a family/friend" applications received in Dublin.
    First tries Selenium for JavaScript content, then falls back to manual setup.
    
    Returns:
        str: The date string found on the website, or None if not found
    """
    url = "https://www.irishimmigration.ie/visa-decisions/"
    
    # Try Selenium first (for JavaScript-loaded content)
    driver = None
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        
        # Initialize the Chrome driver with timeout
        logging.info("Attempting to initialize Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        logging.info("Chrome driver initialized successfully")
        
        # Load the page
        logging.info(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for the specific table to load
        wait = WebDriverWait(driver, 15)
        
        try:
            # Wait for the table with ID "tablepress-8" to appear
            table = wait.until(EC.presence_of_element_located((By.ID, "tablepress-8")))
            logging.info("✅ Found table with ID 'tablepress-8' using Selenium!")
            
            # Find the specific row and column
            target_row = table.find_element(By.CSS_SELECTOR, "tr.row-9")
            logging.info("✅ Found target row with class 'row-9'")
            
            target_cell = target_row.find_element(By.CSS_SELECTOR, "td.column-2")
            logging.info("✅ Found target cell with class 'column-2'")
            
            cell_text = target_cell.text.strip()
            logging.info(f"✅ Cell content: '{cell_text}'")
            
            if cell_text:
                logging.info(f"✅ Successfully extracted date: {cell_text}")
                return cell_text
            else:
                logging.warning("Target cell is empty")
                
        except TimeoutException:
            logging.warning("Table with ID 'tablepress-8' did not load within 15 seconds")
        
        logging.warning("Could not find tourism/family visit date with Selenium")
        return None
        
    except WebDriverException as e:
        logging.error(f"Chrome driver error (may need Chrome installed): {e}")
        return None
    except Exception as e:
        logging.error(f"Selenium error: {e}")
        return None
    finally:
        # Always close the driver
        if driver:
            try:
                driver.quit()
                logging.info("Chrome driver closed successfully")
            except Exception as e:
                logging.warning(f"Error closing driver: {e}")

def load_last_date():
    """
    Load the last known date from the data file.
    
    Returns:
        str: The last known date, or None if file doesn't exist
    """
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_date')
    except Exception as e:
        logging.error(f"Error loading last date: {e}")
    return None

def save_last_date(date_str):
    """
    Save the current date to the data file.
    
    Args:
        date_str (str): The date string to save
    """
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        data = {
            'last_date': date_str,
            'last_updated': datetime.now().isoformat()
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Saved date: {date_str}")
    except Exception as e:
        logging.error(f"Error saving date: {e}")

def send_telegram_notification(old_date, new_date):
    """
    Send a Telegram notification about the date change.
    
    Args:
        old_date (str): The previous date
        new_date (str): The new date
    """
    try:
        # Telegram Bot API endpoint
        url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['bot_token']}/sendMessage"
        
        # Format the message
        message = f"""🚨 *Обновление даты ирландской иммиграционной визы*

📅 *Категория:* Туризм или посещение семьи/друзей

📊 *Детали изменения:*
• Предыдущая дата: `{old_date if old_date else 'Неизвестно'}`
• Новая дата: `{new_date}`

🔗 [Проверьте на сайте](https://www.irishimmigration.ie/visa-decisions/)
⏰ _{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"""

        # Prepare the payload
        payload = {
            'chat_id': TELEGRAM_CONFIG['chat_id'],
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': False
        }
        
        # Send the message
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        # Check if message was sent successfully
        result = response.json()
        if result.get('ok'):
            logging.info("Telegram notification sent successfully")
            return True
        else:
            logging.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
            return False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Telegram notification (network): {e}")
        return False
    except Exception as e:
        logging.error(f"Error sending Telegram notification: {e}")
        return False

def main():
    """Main function to check for date changes and send notifications."""
    logging.info("Starting visa date checker")
    
    # Check if Telegram configuration is properly set
    if not TELEGRAM_CONFIG:
        logging.error("Telegram configuration not loaded. Exiting.")
        return
    
    # Get current date from website
    current_date = get_visa_date()

    # Load last known date
    last_date = load_last_date()
    
    logging.info(f"Current date: {current_date}")
    logging.info(f"Last known date: {last_date}")

    if current_date != last_date:
        # Date has changed - send notification and update saved date
        logging.info(f"Date change detected: {last_date} -> {current_date}")
        print(f"🚨 DATE CHANGE DETECTED: {last_date} -> {current_date}")
        
        # Send Telegram notification
        success = send_telegram_notification(last_date, current_date)
        if success:
            print("📱 Telegram notification sent!")
        else:
            print("❌ Failed to send Telegram notification - check logs")
            
        save_last_date(current_date)
    else:
        # No change
        logging.info("No date change detected")
        print(f"✅ No change detected. Current date: {current_date}")

if __name__ == "__main__":
    main()
