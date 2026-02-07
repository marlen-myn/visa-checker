# Irish Immigration Visa Date Checker

A Python script that automatically monitors the Irish Immigration website for changes in visa processing dates and sends instant Telegram notifications when updates are detected.

## 🎯 What This Script Does

- **Monitors**: Irish Immigration visa decisions page for "Tourism or visit a family/friend" applications
- **Detects**: Changes in "Date applications received in Dublin" 
- **Notifies**: Sends formatted Telegram messages when dates change
- **Tracks**: Stores baseline date and monitors for changes
- **Logs**: All activity for debugging and monitoring

---

## 📱 Telegram Bot Setup (Step-by-Step)

### Step 1: Create Your Telegram Bot

1. **Open Telegram** on your phone or computer
2. **Search for `@BotFather`** (this is Telegram's official bot for creating bots)
3. **Start a chat** with @BotFather
4. **Send the command**: `/newbot`
5. **Choose a name** for your bot (e.g., "Visa Date Checker")
6. **Choose a username** for your bot (must end with "bot", e.g., "visa_date_checker_bot")
7. **Copy the bot token** that BotFather provides (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

#### Option A: For Private Messages (Personal Notifications)

1. **Start a conversation** with your newly created bot
2. **Send any message** to the bot (e.g., "Hello")
3. **Open your web browser** and visit:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Replace `<YOUR_BOT_TOKEN>` with the actual token from Step 1
4. **Look for `"chat":{"id":` in the response**
5. **Copy the number after `"id":`** (this is your chat ID, usually a positive number)

**Example**: If you see `"chat":{"id":123456789,"first_name":"John"...`, your chat ID is `123456789`

#### Option B: For Group Notifications

1. **Create a new Telegram group** or use an existing one
2. **Add your bot to the group**:
   - Go to group settings
   - Add Members
   - Search for your bot username and add it
3. **Send a message mentioning the bot** (e.g., "@your_bot_name hello")
4. **Visit the same URL**:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
5. **Look for the group chat ID** (usually a negative number like `-1001234567890`)

#### Option C: For Channel Notifications (Public or Private)

1. **Create a new Telegram channel** or use an existing one (works for both public and private channels)
2. **Add your bot as an admin** to the channel:
   - Go to channel settings
   - Administrators
   - Add Administrator
   - Search for your bot username and add it
   - **Important**: Give the bot permission to "Post Messages"
3. **Send a message to the channel** (any message will work)
4. **Visit the same URL**:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
5. **Look for the channel chat ID** (usually a negative number like `-1001234567890`)

**Notes**: 
- **Private channels work perfectly** - just follow the same steps above
- For public channels, you can also use the channel username (e.g., `@your_channel_name`) instead of the numeric ID
- **Numeric channel ID is more reliable** and works for both public and private channels
- **Private channel IDs are just as valid** as group IDs - both are negative numbers

### Step 3: Configure the Script

Edit the `checker.py` file and update these values:

```python
TELEGRAM_CONFIG = {
    'bot_token': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',  # Your actual bot token
    'chat_id': '123456789',  # Your actual chat ID (positive for private, negative for groups)
}
```

### Step 4: Test Your Configuration

You can test if your bot configuration works by visiting:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage?chat_id=<YOUR_CHAT_ID>&text=Test message
```

If successful, you'll receive a "Test message" from your bot!

---

## 🖥️ Script Installation & Setup

### 1. Install Required Python Packages

```bash
cd /home/mynz/projects/visa-checker
pip3 install requests beautifulsoup4 selenium
```

### 2. Set the Current Baseline Date

Since the Irish Immigration website uses JavaScript-loaded content, you need to set the current date manually **one time only**:

1. **Visit** https://www.irishimmigration.ie/visa-decisions/
2. **Find the date** for "Tourism or visit a family/friend" applications received in Dublin
3. **Edit `checker.py`** and find line 247:
   ```python
   current_date = '01 February 2025'  # REPLACE WITH ACTUAL DATE FROM WEBSITE
   ```
4. **Replace with the actual date** you found on the website
5. **Save the file**

### 3. Test the Script

```bash
cd /home/mynz/projects/visa-checker
python3 checker.py
```

**On first run**, it will:
- ✅ Try to automatically extract the date using Selenium
- ✅ Use your manually set date if automation fails
- ✅ Save the baseline date to `last_date.json`
- ✅ Create log files for monitoring

**On subsequent runs**, it will:
- ✅ Compare current date with saved baseline
- ✅ Send Telegram notification if date changes
- ✅ Update the stored date

### 4. Schedule Automatic Daily Monitoring

```bash
# Edit your crontab
crontab -e

# Add this line to run daily at 9:00 AM
0 9 * * * /usr/bin/python3 /home/mynz/projects/visa-checker/checker.py

# Or run twice daily (9 AM and 6 PM)
0 9,18 * * * /usr/bin/python3 /home/mynz/projects/visa-checker/checker.py
```

#### Cron Schedule Options:
- `0 9 * * *` - Daily at 9:00 AM
- `0 */6 * * *` - Every 6 hours  
- `0 9,18 * * *` - Twice daily (9 AM and 6 PM)
- `0 9 * * 1-5` - Weekdays only at 9 AM

---

## 🔍 Monitoring Your Script

### Check Recent Activity
```bash
# View recent log entries
tail -20 /home/mynz/projects/visa-checker/checker.log

# Monitor live activity
tail -f /home/mynz/projects/visa-checker/checker.log
```

### Check Current Stored Date
```bash
cat /home/mynz/projects/visa-checker/last_date.json
```

### Manual Test Run
```bash
cd /home/mynz/projects/visa-checker
python3 checker.py
```

---

## 🚨 Testing Telegram Notifications

To test that your Telegram notifications work without waiting for a real change:

### Method 1: Temporary Date Change
```bash
# Edit the stored date to trigger a change detection
echo '{"last_date": "15 January 2025", "last_updated": "2025-01-15T09:00:00"}' > last_date.json

# Run the script - it will detect the change and send notification
python3 checker.py
```

### Method 2: Direct API Test
Visit this URL in your browser (replace with your actual values):
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage?chat_id=<YOUR_CHAT_ID>&text=Test notification from visa checker!
```

---

## 📋 Files Created

- **`checker.py`** - Main monitoring script
- **`last_date.json`** - Stores the last known date for comparison
- **`checker.log`** - Activity logs and debugging information
- **`README.md`** - This setup guide

---

## ❗ Troubleshooting

### "Telegram configuration not set"
- Update the `TELEGRAM_CONFIG` dictionary with your actual bot token and chat ID

### "Could not retrieve current date from website automatically"
- This is expected - the website uses JavaScript
- Follow the manual setup steps above to set the baseline date

### "Failed to send Telegram notification"
- **Check bot token**: Make sure it's correct and includes the full string
- **Check chat ID**: Verify it's the right number (positive for private, negative for groups)
- **Check permissions**: Ensure your bot can send messages to the chat/group
- **Test with browser**: Use the direct API URL method above

### Bot doesn't respond in group
- Make sure the bot has been added to the group
- Check that the bot has permission to send messages
- Verify you're using the correct group chat ID (negative number)

### Cron job not running
```bash
# Check if cron service is running
sudo systemctl status cron

# View your cron jobs
crontab -l

# Check cron logs
grep CRON /var/log/syslog
```

---

## 🔒 Security Notes

- **Keep your bot token secure** - treat it like a password
- **Never share your bot token** publicly or commit it to version control
- **Use environment variables** for production deployments
- **Regularly check your bot's activity** in @BotFather

---

## 🔄 How the Script Works

1. **🌐 Web Scraping**: Attempts to load the visa decisions page with Selenium (JavaScript support)
2. **🔍 Date Extraction**: Looks for table ID `tablepress-8`, row class `row-9`, column class `column-2`  
3. **📊 Change Detection**: Compares current date with previously stored baseline
4. **📱 Notification**: Sends formatted Telegram message when changes detected
5. **💾 Storage**: Updates stored date and logs all activity

The script is designed to run reliably as a daily cron job and will notify you immediately when visa processing dates change!
