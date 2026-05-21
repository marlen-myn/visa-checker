# Irish Immigration Checker

Monitors Irish Immigration website pages and sends Telegram notifications when processing dates change.

## Checkers

| Checker | What it monitors | Config toggle |
|---------|-----------------|---------------|
| **Visa Decisions** | "Tourism or visit a family/friend" — date applications received in Dublin | `visa_checker_enabled` |
| **IRP Renewal** | Submission date currently being processed for a given stamp category | `irp_checker_enabled` |

Both checkers run in a single invocation. Enable or disable each independently in `config.json`.

---

## Quick Start

```bash
# Install dependencies
pip3 install requests selenium

# Configure credentials
cp config.json.example config.json
# Edit config.json with your Telegram bot token and chat ID

# Run
python3 checker.py
```

---

## Configuration

**`config.json`**:

```json
{
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID",
    "visa_checker_enabled": false,
    "irp_checker_enabled": true,
    "irp_stamp_category": "4"
}
```

| Field | Description | Default |
|-------|-------------|---------|
| `bot_token` | Telegram Bot API token (from @BotFather) | *required* |
| `chat_id` | Telegram chat/group/channel ID | *required* |
| `visa_checker_enabled` | Enable visa decisions monitoring | `false` |
| `irp_checker_enabled` | Enable IRP renewal date monitoring | `true` |
| `irp_stamp_category` | Which stamp to track: `"4"`, `"1, 1H"`, `"1G"`, `"2, 2A, 1A"`, `"All other categories"` | `"4"` |

---

## Scheduling (cron)

```bash
crontab -e

# Daily at 9 AM
0 9 * * * /usr/bin/python3 /home/mynz/projects/visa-checker/checker.py

# Twice daily
0 9,18 * * * /usr/bin/python3 /home/mynz/projects/visa-checker/checker.py
```

---

## Monitored Pages

- **Visa Decisions**: https://www.irishimmigration.ie/visa-decisions/
- **IRP Renewal**: https://www.irishimmigration.ie/registering-your-immigration-permission/how-to-renew-your-current-permission/renewing-your-registration-permission-if-you-live-in-the-republic-of-ireland

---

## Files

| File | Purpose |
|------|---------|
| `checker.py` | Main script |
| `config.json` | Credentials and feature toggles (gitignored) |
| `config.json.example` | Template for config.json |
| `last_date.json` | Stored state for change detection |
| `checker.log` | Runtime logs |

---

## How It Works

1. Loads the target page with headless Chrome (Selenium) for JavaScript support
2. Extracts the relevant date from the processing table
3. Compares with the previously stored value in `last_date.json`
4. If changed — sends a formatted Telegram notification and updates stored state
5. If unchanged — logs and exits quietly

---

## Telegram Setup

1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token
2. Start a chat with your bot (or add it to a group/channel)
3. Get your chat ID:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   Look for `"chat":{"id": ...}` in the response
4. Put both values in `config.json`

---

## Troubleshooting

**Script fails to retrieve date**: Chrome/Chromium and chromedriver must be installed and compatible. Check `checker.log` for details.

**No Telegram message received**: Verify `bot_token` and `chat_id`. Test manually:
```
https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=test
```

**Force a test notification**: Edit `last_date.json` to change the stored date, then run the script.
