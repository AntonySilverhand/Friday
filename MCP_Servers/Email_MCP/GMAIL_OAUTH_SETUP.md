# Gmail OAuth2 Setup Guide for Email MCP

This guide walks you through setting up Gmail OAuth2 authentication for Friday's Email MCP server.

## 📋 Prerequisites

- Gmail account with API access
- Google Cloud Console access
- Python environment with required packages

## 🔧 Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project**
   - Click "Select a project" → "New Project"
   - Project name: `Friday-Email-MCP`
   - Click "Create"

3. **Select Your Project**
   - Make sure your new project is selected in the dropdown

### Step 2: Enable Gmail API

1. **Navigate to APIs & Services**
   - In the left menu: "APIs & Services" → "Library"

2. **Search for Gmail API**
   - Search: "Gmail API"
   - Click on "Gmail API" result

3. **Enable the API**
   - Click "Enable" button
   - Wait for confirmation

### Step 3: Create OAuth2 Credentials

1. **Go to Credentials**
   - Left menu: "APIs & Services" → "Credentials"

2. **Create Credentials**
   - Click "Create Credentials" → "OAuth client ID"

3. **Configure OAuth Consent Screen** (if not done)
   - Click "Configure Consent Screen"
   - Choose "External" (for personal use)
   - Fill required fields:
     - App name: `Friday AI Email Management`
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Click "Save and Continue" (we'll add scopes in code)
   - Test users: Add your email address
   - Click "Save and Continue"

4. **Create OAuth Client ID**
   - Application type: "Desktop application"
   - Name: `Friday Email MCP Client`
   - Click "Create"

5. **Download Credentials**
   - Click "Download JSON" for your new client ID
   - Save as `credentials.json` in your project directory

### Step 4: Install Dependencies

```bash
cd MCP_Servers/Email_MCP
pip install -r requirements.txt
```

### Step 5: Configure Environment

1. **Move credentials file**
   ```bash
   # Move the downloaded file to your project directory
   mv ~/Downloads/credentials.json /root/coding/Friday/MCP_Servers/Email_MCP/
   ```

2. **Update .env file**
   ```env
   # Add to your .env file
   GMAIL_CREDENTIALS_PATH=MCP_Servers/Email_MCP/credentials.json
   GMAIL_TOKEN_PATH=MCP_Servers/Email_MCP/token.pickle
   ```

### Step 6: First-Time Authentication

1. **Run the Email MCP server**
   ```bash
   python MCP_Servers/Email_MCP/email_mcp_server.py
   ```

2. **Complete OAuth Flow**
   - A browser window will open automatically
   - Sign in to your Gmail account
   - Grant permissions to the app
   - You'll see "The authentication flow has completed"

3. **Verify Authentication**
   - Check for `token.pickle` file creation
   - Server should start without errors

## 🔐 Required Scopes

The Email MCP server requires these Gmail API scopes:

- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify emails (mark as read, archive, etc.)

## 📁 File Structure

After setup, your directory should look like:

```
MCP_Servers/Email_MCP/
├── email_mcp_server.py
├── requirements.txt
├── credentials.json          # OAuth2 credentials (keep secure)
├── token.pickle             # Access token (auto-generated)
├── GMAIL_OAUTH_SETUP.md     # This guide
└── email_server.log         # Server logs
```

## 🛠️ Troubleshooting

### Common Issues

#### **"credentials.json not found"**
- Ensure you downloaded the credentials file from Google Cloud Console
- Check the file path in your .env file
- Verify the file is in the correct directory

#### **"Access blocked: This app's request is invalid"**
- Make sure your OAuth consent screen is properly configured
- Add your email to test users list
- Check that Gmail API is enabled

#### **"insufficient_scope" Error**
- Delete `token.pickle` file
- Restart the server to re-authenticate
- Make sure all required scopes are requested

#### **Browser doesn't open for OAuth**
- Check your display settings if using SSH
- Use port forwarding: `ssh -L 8080:localhost:8080 user@host`
- Run authentication on local machine and copy `token.pickle`

### Debug Mode

Enable detailed logging:

```python
# In email_mcp_server.py
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Best Practices

### Credential Management
- **Never commit credentials.json to version control**
- **Keep token.pickle secure** - it contains access tokens
- **Use environment variables** for file paths
- **Regularly rotate credentials** in production

### Access Control
- **Use principle of least privilege** - only request needed scopes
- **Monitor API usage** in Google Cloud Console
- **Set up alerts** for unusual activity
- **Review OAuth consent screen** regularly

### .gitignore Entries
Add these to your .gitignore:
```
# Gmail OAuth credentials
credentials.json
token.pickle
*.log
```

## 📊 API Limits

### Gmail API Quotas
- **Daily quota**: 1,000,000,000 quota units
- **Per-user rate limit**: 250 quota units per user per second
- **Batch requests**: Up to 100 operations per batch

### Rate Limiting
The server implements automatic rate limiting and retry logic for API calls.

## 🧪 Testing Your Setup

### Quick Test Commands

```bash
# Test server startup
python email_mcp_server.py

# Test API access (from another terminal)
curl "http://127.0.0.1:5002/health"

# Test with Friday
python friday_with_memory.py
# Then ask: "Check my recent emails"
```

### Verification Checklist

- [ ] ✅ Google Cloud project created
- [ ] ✅ Gmail API enabled
- [ ] ✅ OAuth2 credentials downloaded
- [ ] ✅ Dependencies installed
- [ ] ✅ First-time authentication completed
- [ ] ✅ token.pickle file created
- [ ] ✅ Server starts without errors
- [ ] ✅ Can retrieve emails through MCP
- [ ] ✅ Can send emails through MCP

## 🚀 Production Deployment

For production use:

1. **Use service account** instead of OAuth2
2. **Set up proper logging** and monitoring
3. **Implement rate limiting** in your application
4. **Use environment-specific credentials**
5. **Set up automated token refresh**

## 📚 Additional Resources

- **Gmail API Documentation**: https://developers.google.com/gmail/api
- **OAuth2 for Desktop Apps**: https://developers.google.com/identity/protocols/oauth2/native-app
- **Google Cloud Console**: https://console.cloud.google.com/
- **API Quotas & Limits**: https://developers.google.com/gmail/api/reference/quota

## 🆘 Support

If you encounter issues:

1. **Check the logs**: `email_server.log`
2. **Verify credentials**: Re-download from Google Cloud Console
3. **Test API access**: Use Google's API Explorer
4. **Check quotas**: Review usage in Google Cloud Console

Remember: Keep your credentials secure and never share them publicly!