# 🤖 Friday AI - Telegram Integration Setup Guide

Follow this step-by-step guide to set up Telegram messaging integration with your Friday AI Assistant.

## 📋 Setup Checklist

### ✅ Phase 1: Telegram Bot Creation (High Priority)

#### **Task 1: Create Telegram Bot with @BotFather**
1. Open Telegram app on your phone/computer
2. Search for `@BotFather` (official Telegram bot for creating bots)
3. Start a conversation with @BotFather
4. Send `/start` command
5. Send `/newbot` command to create a new bot

**Expected Result**: BotFather will ask for your bot's name and username

---

#### **Task 2: Get Bot Token from BotFather**
1. **Bot Name**: Choose a display name (e.g., "Antony's Friday Assistant")
2. **Bot Username**: Choose a unique username ending in 'bot' (e.g., "antony_friday_bot")
3. **Save the Token**: BotFather will provide a token like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

**⚠️ IMPORTANT**: Keep this token secure - it gives full access to your bot!

**Expected Result**: You'll receive a message with your bot token

---

#### **Task 3: Find Your Telegram Chat ID**

**Method 1: Using Web Browser**
1. Send any message to your new bot (e.g., "Hello")
2. Open this URL in browser: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Replace `<YOUR_BOT_TOKEN>` with your actual token
4. Look for `"chat":{"id":` followed by a number (e.g., `123456789`)
5. Save this number - it's your chat ID

**Method 2: Using @userinfobot**
1. Search for `@userinfobot` on Telegram
2. Send `/start` to the bot
3. It will reply with your user ID (same as chat ID for private chats)

**Expected Result**: You'll have a numeric chat ID (positive for private chats)

---

#### **Task 4: Create .env File with Telegram Credentials**

1. **Navigate to your Friday project directory**:
   ```bash
   cd /path/to/Friday
   ```

2. **Create or edit .env file**:
   ```bash
   nano .env
   ```

3. **Add these lines** (replace with your actual values):
   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Gmail Configuration (existing)
   GMAIL_USER=your_gmail_address@gmail.com
   GMAIL_APP_PASSWORD=your_gmail_app_password
   
   # Telegram Configuration (NEW)
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   ```

4. **Save and exit** (Ctrl+X, then Y, then Enter in nano)

**Expected Result**: .env file contains all necessary credentials

---

### ✅ Phase 2: Installation & Testing (Medium Priority)

#### **Task 5: Install Telegram MCP Dependencies**

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Install required packages**:
   ```bash
   pip install -r MCP_Servers/Telegram_MCP/requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python -c "import telegram; print('Telegram library installed successfully')"
   ```

**Expected Result**: All dependencies installed without errors

---

#### **Task 6: Test Telegram Bot Basic Functionality**

1. **Run the integration test**:
   ```bash
   python test_telegram_integration.py
   ```

2. **Check test results** - should show:
   ```
   📊 TELEGRAM INTEGRATION TEST RESULTS
   Success Rate: 100.0%
   ```

3. **Send a test message to your bot**:
   - Open Telegram
   - Find your bot (search for the username you created)
   - Send `/start` command
   - Send any message like "Hello Friday"

**Expected Result**: Bot responds and test passes

---

#### **Task 7: Start Telegram MCP Server**

1. **Start the MCP server**:
   ```bash
   python MCP_Servers/Telegram_MCP/telegram_mcp_server.py
   ```

2. **Look for these success messages**:
   ```
   Starting Telegram MCP server on 127.0.0.1:5001
   Telegram bot started and listening for messages
   ```

3. **Keep this terminal open** - the server needs to run continuously

**Expected Result**: Server running and monitoring messages

---

#### **Task 8: Test Friday Telegram Integration**

1. **Open a new terminal** (keep MCP server running in the first one)

2. **Test Friday with Telegram**:
   ```bash
   python friday_with_memory.py
   ```

3. **Try these Friday commands**:
   ```python
   # In the Friday interface, try:
   friday.get_response("Check my recent Telegram messages")
   friday.get_response("Send a Telegram message saying 'Friday is now connected!'")
   friday.get_response("Show me my Telegram chats")
   ```

**Expected Result**: Friday can access and send Telegram messages

---

### ✅ Phase 3: Verification & Advanced Features (Low Priority)

#### **Task 9: Verify Message Retrieval and Sending**

1. **Send yourself messages** from another device/account
2. **Test retrieval**:
   ```python
   friday.get_response("What are my recent Telegram messages?")
   ```
3. **Test sending**:
   ```python
   friday.get_response("Reply to the last message saying 'Got it!'")
   ```
4. **Test search**:
   ```python
   friday.get_response("Search my Telegram messages for 'important'")
   ```

**Expected Result**: All message operations work correctly

---

#### **Task 10: Configure Advanced Features (Optional)**

**A. Increase Message Cache**:
```python
# In telegram_mcp_server.py, modify:
self.cache_limit = 500  # Increase from default 100
```

**B. Add Webhook Support** (for production):
```python
# Set webhook instead of polling
await application.bot.set_webhook("https://your-domain.com/webhook")
```

**C. Custom Message Handlers**:
```python
# Add handlers for photos, documents, etc.
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
```

**Expected Result**: Enhanced functionality based on your needs

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### **Bot Token Issues**
- ❌ **Error**: "Bot token invalid"
- ✅ **Solution**: Double-check token format, regenerate if needed

#### **Chat ID Issues**
- ❌ **Error**: "Chat not found"
- ✅ **Solution**: Send a message to bot first, then get updates

#### **Server Connection Issues**
- ❌ **Error**: "Connection refused to localhost:5001"
- ✅ **Solution**: Ensure MCP server is running in background

#### **Import Errors**
- ❌ **Error**: "No module named 'telegram'"
- ✅ **Solution**: Run `pip install python-telegram-bot` in venv

### **Verification Commands**

```bash
# Check if bot token works
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Check recent updates
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"

# Test MCP server
curl "http://127.0.0.1:5001/health"
```

---

## 🚀 Usage Examples

Once setup is complete, Friday can:

### **Message Management**
```python
# Get recent messages
"What are my Telegram messages from the last hour?"

# Send a message
"Send a Telegram message: 'In a meeting, will respond in 30 minutes'"

# Reply to specific message
"Reply to the message about the project deadline saying 'Confirmed for Friday'"
```

### **Message Search**
```python
# Search by keyword
"Find Telegram messages mentioning 'budget'"

# Search by timeframe
"Show me Telegram messages from yesterday about the presentation"
```

### **Chat Management**
```python
# Get chat overview
"Show me my most active Telegram chats"

# Get specific chat messages
"What are the recent messages in my work group chat?"
```

---

## 📊 Final Verification Checklist

- [ ] ✅ Bot created and token obtained
- [ ] ✅ Chat ID identified and saved
- [ ] ✅ .env file configured with credentials
- [ ] ✅ Dependencies installed successfully
- [ ] ✅ Integration tests pass (100% success rate)
- [ ] ✅ MCP server starts without errors
- [ ] ✅ Friday can retrieve Telegram messages
- [ ] ✅ Friday can send Telegram messages
- [ ] ✅ Message search functionality works
- [ ] ✅ Bot responds to commands in Telegram

---

## 🔒 Security Notes

- **Never share your bot token** - treat it like a password
- **Use environment variables** - don't hardcode credentials
- **Regular token rotation** - regenerate tokens periodically
- **Monitor bot activity** - check logs for unusual activity
- **Limit bot permissions** - only grant necessary access

---

## 📚 Additional Resources

- **Telegram Bot API Documentation**: https://core.telegram.org/bots/api
- **python-telegram-bot Library**: https://python-telegram-bot.readthedocs.io/
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp
- **Friday AI Repository**: [Your GitHub repository]

---

## 🆘 Support

If you encounter issues:

1. **Check the logs**: `tail -f telegram_server.log`
2. **Run diagnostics**: `python test_telegram_integration.py`
3. **Verify credentials**: Check .env file format
4. **Restart services**: Stop and restart MCP server

**Need help?** Create an issue in the Friday AI repository with:
- Error messages
- Log files
- Steps to reproduce
- Your system configuration

---

*🎉 Once completed, your Friday AI Assistant will have full Telegram integration capabilities!*