# Email Management MCP Server for Friday AI Assistant

This MCP (Model Context Protocol) server provides comprehensive email management capabilities for Friday AI Assistant through the Gmail API, enabling full inbox access, message management, and automated email operations.

## 🚀 Features

### 📧 Email Operations
- **Inbox Access**: Read and retrieve emails from Gmail
- **Email Search**: Advanced search with Gmail query syntax
- **Email Sending**: Send emails with text/HTML content and attachments
- **Email Management**: Mark as read/unread, archive, delete emails
- **Label Management**: Access and work with Gmail labels

### 🔍 Advanced Capabilities
- **OAuth2 Authentication**: Secure access with proper scopes
- **Attachment Support**: Handle file attachments in sent and received emails
- **Rich Formatting**: Support for both text and HTML email content
- **Batch Operations**: Process multiple emails efficiently
- **Smart Parsing**: Extract headers, body content, and metadata

### 🤖 AI Integration
- **Timeline Integration**: Works with Friday's memory system
- **Smart Formatting**: AI-friendly email presentation
- **Context Awareness**: Maintains conversation context for email threads

## 🛠️ MCP Tools Available

### `get_recent_emails`
Retrieve recent emails from Gmail inbox.
- **Parameters**: `limit` (int), `hours_back` (int), `unread_only` (bool)
- **Returns**: Formatted timeline of recent emails with metadata

### `search_emails`
Search emails using Gmail query syntax.
- **Parameters**: `query` (required), `limit` (int), `hours_back` (int)
- **Returns**: Formatted search results with email details

### `read_email`
Read a specific email by message ID.
- **Parameters**: `message_id` (required)
- **Returns**: Full email content including headers, body, and attachments

### `send_email`
Send an email through Gmail API.
- **Parameters**: `to` (required), `subject` (required), `body` (required), `cc` (optional), `bcc` (optional), `html_body` (optional)
- **Returns**: Send confirmation with message ID

### `mark_emails_as_read`
Mark emails as read.
- **Parameters**: `message_ids` (comma-separated list)
- **Returns**: Operation status

### `archive_emails`
Archive emails (remove from inbox).
- **Parameters**: `message_ids` (comma-separated list)
- **Returns**: Operation status

### `get_gmail_labels`
Get all Gmail labels.
- **Returns**: List of available labels with IDs

## 📋 Setup Instructions

### Step 1: Google Cloud Setup
1. **Create Google Cloud Project**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project: "Friday-Email-MCP"

2. **Enable Gmail API**
   - Navigate to "APIs & Services" → "Library"
   - Search and enable "Gmail API"

3. **Create OAuth2 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Create OAuth client ID for Desktop application
   - Download credentials as `credentials.json`

### Step 2: Local Setup
1. **Install Dependencies**
   ```bash
   cd MCP_Servers/Email_MCP
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Add to .env file
   GMAIL_CREDENTIALS_PATH=MCP_Servers/Email_MCP/credentials.json
   GMAIL_TOKEN_PATH=MCP_Servers/Email_MCP/token.pickle
   ```

3. **Place Credentials**
   ```bash
   mv ~/Downloads/credentials.json MCP_Servers/Email_MCP/
   ```

### Step 3: First-Time Authentication
1. **Start Email MCP Server**
   ```bash
   python MCP_Servers/Email_MCP/email_mcp_server.py
   ```

2. **Complete OAuth Flow**
   - Browser will open automatically
   - Sign in and grant permissions
   - `token.pickle` will be created automatically

### Step 4: Integration with Friday
The Email MCP is already integrated in Friday's configuration:
```python
{
    "type": "mcp",
    "server_label": "email",
    "server_url": "http://127.0.0.1:5002/mcp",
    "require_approval": "never",
}
```

## 💡 Usage Examples

### Email Retrieval
```python
# Get recent emails
response = friday.get_response("Check my recent emails from the last 6 hours")

# Search for specific emails
response = friday.get_response("Search my emails for 'project deadline'")

# Read a specific email
response = friday.get_response("Read email with ID 123abc456def")
```

### Email Management
```python
# Send an email
response = friday.get_response("Send an email to john@example.com with subject 'Meeting Tomorrow' and body 'Let's meet at 2 PM'")

# Mark emails as read
response = friday.get_response("Mark emails 123abc, 456def as read")

# Archive emails
response = friday.get_response("Archive the emails about the old project")
```

### Advanced Operations
```python
# Get unread emails only
response = friday.get_response("Show me only unread emails from today")

# Search with complex queries
response = friday.get_response("Find emails from boss@company.com about budget from last week")

# Get label information
response = friday.get_response("Show me all my Gmail labels")
```

## 🔐 Security & Authentication

### OAuth2 Scopes
- `gmail.readonly` - Read access to emails
- `gmail.send` - Send emails
- `gmail.modify` - Modify emails (mark as read, archive, etc.)

### Credential Security
- **credentials.json**: OAuth2 client credentials (keep secure)
- **token.pickle**: Access/refresh tokens (auto-managed)
- **Environment variables**: Secure path configuration

### Best Practices
- Never commit credentials to version control
- Use environment-specific credential files
- Monitor API usage in Google Cloud Console
- Set up proper .gitignore entries

## 🔧 Configuration

### Server Settings
```python
# In email_mcp_server.py
mcp = FastMCP(
    name="email-mcp",
    host="127.0.0.1",
    port=5002,
    timeout=30
)
```

### File Paths
```env
GMAIL_CREDENTIALS_PATH=MCP_Servers/Email_MCP/credentials.json
GMAIL_TOKEN_PATH=MCP_Servers/Email_MCP/token.pickle
```

## 🧪 Testing

### Run Integration Tests
```bash
python test_email_integration.py
```

### Test Components
- Environment setup verification
- Gmail API library imports
- OAuth credentials validation
- Email server creation
- MCP tools registration
- Friday integration check

### Expected Results
- 100% pass rate for code structure tests
- OAuth flow completion
- Server startup without errors

## 🐛 Troubleshooting

### Common Issues

#### **"credentials.json not found"**
- Download from Google Cloud Console
- Check file path in .env
- Verify file permissions

#### **OAuth Flow Fails**
- Check OAuth consent screen configuration
- Add your email to test users
- Ensure Gmail API is enabled

#### **"insufficient_scope" Error**
- Delete token.pickle
- Restart server to re-authenticate
- Verify all scopes are requested

#### **Server Won't Start**
- Check port 5002 availability
- Verify all dependencies installed
- Review server logs

### Debug Commands
```bash
# Check credentials format
python -c "import json; print(json.load(open('credentials.json'))['installed'].keys())"

# Test Gmail API access
curl "https://www.googleapis.com/gmail/v1/users/me/profile" -H "Authorization: Bearer $(cat token.pickle)"

# Verify server health
curl "http://127.0.0.1:5002/health"
```

## 📊 API Limits & Performance

### Gmail API Quotas
- **Daily quota**: 1 billion quota units
- **Per-user rate**: 250 quota units/second
- **Batch operations**: Up to 100 per batch

### Performance Optimization
- Automatic retry with exponential backoff
- Batch processing for multiple operations
- Efficient message parsing and caching
- Minimal API calls through smart caching

## 🔄 Differences from SMTP Version

### Old SMTP Implementation
- ✅ Send emails only
- ❌ No inbox access
- ❌ No email management
- ❌ Basic authentication

### New Gmail API Implementation
- ✅ Full inbox access
- ✅ Advanced email search
- ✅ Email management (read/archive/delete)
- ✅ OAuth2 security
- ✅ Attachment handling
- ✅ Rich metadata access
- ✅ Label management

## 🚀 Future Enhancements

### Planned Features
- **Email threading**: Group related emails
- **Smart filters**: AI-powered email categorization
- **Scheduled sending**: Send emails at specific times
- **Template management**: Reusable email templates
- **Webhook support**: Real-time email notifications

### Integration Possibilities
- **Calendar integration**: Extract meeting invites
- **Contact management**: Update contact information
- **Task creation**: Convert emails to tasks
- **Document extraction**: Save email attachments

## 📚 Resources

- **Gmail API Documentation**: https://developers.google.com/gmail/api
- **OAuth2 Guide**: https://developers.google.com/identity/protocols/oauth2
- **Google Cloud Console**: https://console.cloud.google.com/
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp

## 📄 License

This Email MCP server is part of the Friday AI Assistant project and follows the same licensing terms.

---

**🎉 With this Email MCP, Friday now has complete email management capabilities, from reading your inbox to sending professional emails with attachments!**