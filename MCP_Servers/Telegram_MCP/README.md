# Telegram MCP Server for Friday AI Assistant

This MCP (Model Context Protocol) server enables Friday AI Assistant to interact with Telegram, allowing message retrieval and automated responses through the Telegram Bot API.

## Features

### 📱 Message Management
- **Message Retrieval**: Get recent messages from Telegram chats
- **Message Sending**: Send messages and replies through your bot
- **Message Search**: Search through message history by keywords
- **Chat Information**: View available chats and their activity

### 🤖 AI Integration
- **Automatic Caching**: Incoming messages are automatically cached for quick access
- **Smart Formatting**: Messages are formatted for easy AI consumption
- **Timeline Integration**: Works with Friday's memory system for context

### 🔧 MCP Tools Available

#### `get_recent_telegram_messages`
Retrieve recent messages from Telegram chats.
- **Parameters**: `limit` (int), `hours_back` (int), `chat_id` (int, optional)
- **Returns**: Formatted timeline of recent messages

#### `send_telegram_message`
Send a message through Telegram.
- **Parameters**: `text` (required), `chat_id` (optional), `reply_to_message_id` (optional), `formatting` (optional)
- **Returns**: Success/failure status with message details

#### `search_telegram_messages`
Search messages by text content.
- **Parameters**: `query` (required), `limit` (int), `hours_back` (int)
- **Returns**: Formatted search results with highlighted matches

#### `get_telegram_chats`
Get information about available chats.
- **Returns**: List of chats with activity information

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Save the bot token provided by BotFather

### 2. Get Your Chat ID

1. Send a message to your bot
2. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your chat ID in the response

### 3. Environment Configuration

Create a `.env` file in your project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 4. Install Dependencies

```bash
cd MCP_Servers/Telegram_MCP
pip install -r requirements.txt
```

### 5. Run the Server

```bash
python telegram_mcp_server.py
```

The server will start on `127.0.0.1:5001` and begin monitoring for Telegram messages.

## Integration with Friday AI

### Adding to Friday's Tool Set

Add the Telegram MCP server to Friday's configuration:

```python
# In friday_with_memory.py, add to tools configuration:
{
    "type": "mcp",
    "server_label": "telegram",
    "server_url": "http://127.0.0.1:5001/mcp",
    "require_approval": "never",
}
```

### Example Usage

Once integrated, Friday can:

```python
# Retrieve recent messages
response = friday.get_response("Check my recent Telegram messages")

# Send a message
response = friday.get_response("Send a Telegram message saying 'Hello from Friday!'")

# Search for specific content
response = friday.get_response("Search my Telegram messages for 'meeting'")

# Get chat information
response = friday.get_response("Show me my Telegram chats")
```

## Security Considerations

### Bot Permissions
- The bot only has access to messages sent to it directly
- Cannot read messages from groups unless added as admin
- Cannot access messages from other users' private chats

### Data Handling
- Messages are cached locally for quick access
- Cache is limited to 100 recent messages by default
- No sensitive data is logged in plain text
- All API calls use HTTPS encryption

### Access Control
- Bot token should be kept secure and not shared
- Chat ID restricts which conversations the bot can access
- Environment variables prevent credential exposure

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | Yes |
| `TELEGRAM_CHAT_ID` | Your personal chat ID | Recommended |

### Server Configuration

```python
# In telegram_mcp_server.py
mcp = FastMCP(
    name="telegram-mcp",
    host="127.0.0.1",      # Server host
    port=5001,             # Server port
    timeout=30             # Request timeout
)

# Message cache settings
cache_limit = 100          # Maximum cached messages
```

## Troubleshooting

### Common Issues

1. **Bot Not Responding**
   - Verify `TELEGRAM_BOT_TOKEN` is correct
   - Check that bot is not blocked
   - Ensure bot has necessary permissions

2. **Messages Not Cached**
   - Send a message to the bot first
   - Check server logs for errors
   - Verify bot is polling correctly

3. **Send Message Fails**
   - Verify `TELEGRAM_CHAT_ID` is correct
   - Check bot permissions in the target chat
   - Ensure message text is not empty

### Debug Mode

Enable detailed logging by setting log level:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

- `telegram_server.log` - Server activity and errors
- Check console output for real-time status

## API Limitations

### Telegram Bot API Limits
- 30 messages per second to different chats
- 1 message per second to the same chat
- Message size limit: 4096 characters
- File size limit: 50 MB

### MCP Server Limits
- Message cache: 100 messages (configurable)
- Search history: 1 week by default
- Concurrent connections: Handled by FastMCP

## Advanced Features

### Custom Message Handlers

Add custom handlers for specific message types:

```python
# In telegram_mcp_server.py
async def handle_photo_message(update, context):
    # Handle photo messages
    pass

application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
```

### Webhook Support

For production deployment, consider using webhooks instead of polling:

```python
# Set webhook URL
await application.bot.set_webhook("https://your-domain.com/webhook")
```

### Database Integration

For persistent message storage, integrate with Friday's memory system:

```python
# Store messages in Friday's timeline
telegram_server.memory_manager.store_conversation(entry)
```

## License

This Telegram MCP server is part of the Friday AI Assistant project.

## Support

For issues and feature requests, please check the main Friday AI repository or create an issue with detailed information about your setup and the problem encountered.