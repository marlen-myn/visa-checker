#!/usr/bin/env python3
"""
Irish Immigration Checker

Monitors two Irish Immigration pages and sends Telegram notifications on changes:
1. Visa decisions — "Tourism or visit a family/friend" processing date
2. IRP renewal — submission date currently being processed per stamp category

Each checker is toggled on/off via config.json.

Usage: python3 checker.py
Schedule: 0 9 * * * /usr/bin/python3 /path/to/checker.py
"""

import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException

# Paths relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
DATA_FILE = os.path.join(SCRIPT_DIR, "last_date.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "checker.log")

# Target URLs
VISA_DECISIONS_URL = "https://www.irishimmigration.ie/visa-decisions/"
IRP_RENEWAL_URL = (
    "https://www.irishimmigration.ie/registering-your-immigration-permission/"
    "how-to-renew-your-current-permission/"
    "renewing-your-registration-permission-if-you-live-in-the-republic-of-ireland"
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION & DATA
# =============================================================================


def load_config():
    """Load and validate configuration from config.json."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        logger.error("config.json not found. Copy config.json.example and fill in credentials.")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config.json: {e}")
        return None

    if not config.get("bot_token") or not config.get("chat_id"):
        logger.error("config.json must contain non-empty 'bot_token' and 'chat_id'")
        return None

    return config


def load_data():
    """Load stored state from the data file."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading data file: {e}")
    return {}


def save_data(data):
    """Persist state to the data file."""
    try:
        data["last_updated"] = datetime.now().isoformat()
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        logger.error(f"Error saving data file: {e}")


# =============================================================================
# SELENIUM HELPERS
# =============================================================================


@contextmanager
def chrome_driver():
    """Context manager for a headless Chrome WebDriver."""
    options = Options()
    for arg in [
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--disable-extensions",
        "--disable-logging",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
    ]:
        options.add_argument(arg)

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        yield driver
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


# =============================================================================
# TELEGRAM
# =============================================================================


def send_telegram(config, message):
    """Send a message via Telegram Bot API. Returns True on success."""
    url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
    payload = {
        "chat_id": config["chat_id"],
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            logger.info("Telegram notification sent")
            return True
        logger.error(f"Telegram API error: {result.get('description')}")
    except requests.RequestException as e:
        logger.error(f"Telegram request failed: {e}")
    return False


# =============================================================================
# VISA DECISIONS CHECKER
# =============================================================================


def get_visa_date():
    """
    Scrape visa decisions page for "Tourism or visit a family/friend"
    date applications received in Dublin.
    """
    try:
        with chrome_driver() as driver:
            logger.info(f"Loading: {VISA_DECISIONS_URL}")
            driver.get(VISA_DECISIONS_URL)

            wait = WebDriverWait(driver, 15)
            table = wait.until(EC.presence_of_element_located((By.ID, "tablepress-8")))

            target_row = table.find_element(By.CSS_SELECTOR, "tr.row-9")
            target_cell = target_row.find_element(By.CSS_SELECTOR, "td.column-2")
            cell_text = target_cell.text.strip()

            if cell_text:
                logger.info(f"Visa date extracted: {cell_text}")
                return cell_text

            logger.warning("Visa target cell is empty")
    except (WebDriverException, TimeoutException) as e:
        logger.error(f"Visa checker error: {e}")
    except Exception as e:
        logger.error(f"Unexpected visa checker error: {e}")
    return None


def run_visa_checker(config, data):
    """Run the visa decisions checker. Returns True if data was updated."""
    logger.info("--- Visa Decisions Checker: ENABLED ---")
    current = get_visa_date()

    if current is None:
        print("❌ Visa checker: failed to retrieve date")
        return False

    previous = data.get("visa_last_date")
    logger.info(f"Visa date — current: {current}, previous: {previous}")

    if current == previous:
        print(f"✅ Visa checker: no change. Date: {current}")
        return False

    print(f"🚨 VISA DATE CHANGE: {previous} -> {current}")

    message = (
        f"🚨 *Обновление даты ирландской иммиграционной визы*\n\n"
        f"📅 *Категория:* Туризм или посещение семьи/друзей\n\n"
        f"📊 *Детали изменения:*\n"
        f"• Предыдущая дата: `{previous or 'Неизвестно'}`\n"
        f"• Новая дата: `{current}`\n\n"
        f"🔗 [Проверьте на сайте]({VISA_DECISIONS_URL})\n"
        f"⏰ _{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    )

    if send_telegram(config, message):
        print("📱 Visa notification sent!")
    else:
        print("❌ Failed to send visa notification")

    data["visa_last_date"] = current
    return True


# =============================================================================
# IRP RENEWAL CHECKER
# =============================================================================


def get_irp_renewal_date(stamp_category):
    """
    Scrape IRP renewal page for the submission date currently being
    processed for the given stamp category.
    """
    try:
        with chrome_driver() as driver:
            logger.info(f"Loading: {IRP_RENEWAL_URL}")
            driver.get(IRP_RENEWAL_URL)

            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

            # Wait for DataTable cells to populate
            wait.until(
                lambda d: any(
                    cell.text.strip()
                    for cell in d.find_elements(By.CSS_SELECTOR, "table td")
                )
            )

            table = driver.find_element(By.CSS_SELECTOR, "table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            logger.info(f"IRP table: {len(rows)} rows")

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    category = cells[0].text.strip()
                    date_text = cells[1].text.strip()
                    if category == stamp_category:
                        logger.info(f"IRP Stamp {stamp_category}: {date_text}")
                        return date_text

            logger.warning(f"Stamp {stamp_category} not found in IRP table")
    except (WebDriverException, TimeoutException) as e:
        logger.error(f"IRP checker error: {e}")
    except Exception as e:
        logger.error(f"Unexpected IRP checker error: {e}")
    return None


def run_irp_checker(config, data, stamp_category):
    """Run the IRP renewal checker. Returns True if data was updated."""
    logger.info(f"--- IRP Renewal Checker (Stamp {stamp_category}): ENABLED ---")
    current = get_irp_renewal_date(stamp_category)

    if current is None:
        print("❌ IRP checker: failed to retrieve date")
        return False

    previous = data.get("irp_last_date")
    logger.info(f"IRP date (Stamp {stamp_category}) — current: {current}, previous: {previous}")

    if current == previous:
        print(f"✅ IRP checker (Stamp {stamp_category}): no change. Date: {current}")
        return False

    print(f"🚨 IRP DATE CHANGE (Stamp {stamp_category}): {previous} -> {current}")

    message = (
        f"🚨 *Обновление даты IRP Renewal (Stamp {stamp_category})*\n\n"
        f"📅 *Категория:* Stamp {stamp_category}\n\n"
        f"📊 *Детали изменения:*\n"
        f"• Предыдущая дата рассмотрения: `{previous or 'Неизвестно'}`\n"
        f"• Новая дата рассмотрения: `{current}`\n\n"
        f"ℹ️ Это дата подачи заявлений, которые сейчас обрабатываются. "
        f"Если ваша заявка подана до этой даты — она должна быть обработана.\n\n"
        f"🔗 [Проверьте на сайте]({IRP_RENEWAL_URL})\n"
        f"⏰ _{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    )

    if send_telegram(config, message):
        print("📱 IRP notification sent!")
    else:
        print("❌ Failed to send IRP notification")

    data["irp_last_date"] = current
    data["irp_stamp_category"] = stamp_category
    return True


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Entry point — runs enabled checkers and persists state on changes."""
    logger.info("=" * 60)
    logger.info("Starting Irish Immigration Checker")
    logger.info("=" * 60)

    config = load_config()
    if not config:
        return

    visa_enabled = config.get("visa_checker_enabled", False)
    irp_enabled = config.get("irp_checker_enabled", True)
    irp_stamp = config.get("irp_stamp_category", "4")

    data = load_data()
    changed = False

    # Visa decisions
    if visa_enabled:
        changed |= run_visa_checker(config, data)
    else:
        logger.info("--- Visa Decisions Checker: DISABLED ---")
        print("⏸️  Visa checker: disabled")

    # IRP renewal
    if irp_enabled:
        changed |= run_irp_checker(config, data, irp_stamp)
    else:
        logger.info("--- IRP Renewal Checker: DISABLED ---")
        print("⏸️  IRP checker: disabled")

    if changed:
        save_data(data)

    logger.info("Run complete")


if __name__ == "__main__":
    main()
