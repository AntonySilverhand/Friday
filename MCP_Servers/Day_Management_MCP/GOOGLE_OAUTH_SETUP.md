# Google Calendar & Tasks OAuth2 Setup Guide for Day Management MCP

This guide walks you through setting up Google Calendar and Tasks OAuth2 authentication for Friday's Day Management MCP server.

## 📋 Prerequisites

- Google account with Calendar and Tasks access
- Google Cloud Console access
- Python environment with required packages

## 🔧 Step-by-Step Setup

### Step 1: Create Google Cloud Project (or use existing)

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project or Select Existing**
   - If creating new: Project name: `Friday-Day-Management`
   - If using existing: Select your Friday project
   - Click "Create" or select project

### Step 2: Enable Required APIs

1. **Navigate to APIs & Services**
   - In the left menu: "APIs & Services" → "Library"

2. **Enable Google Calendar API**
   - Search: "Google Calendar API"
   - Click on "Google Calendar API" result
   - Click "Enable" button

3. **Enable Google Tasks API**
   - Search: "Google Tasks API"
   - Click on "Google Tasks API" result
   - Click "Enable" button

### Step 3: Create OAuth2 Credentials

1. **Go to Credentials**
   - Left menu: "APIs & Services" → "Credentials"

2. **Create Credentials**
   - Click "Create Credentials" → "OAuth client ID"

3. **Configure OAuth Consent Screen** (if not done)
   - Click "Configure Consent Screen"
   - Choose "External" (for personal use)
   - Fill required fields:
     - App name: `Friday AI Day Management`
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Click "Add or Remove Scopes"
     - Add these scopes:
       - `https://www.googleapis.com/auth/calendar`
       - `https://www.googleapis.com/auth/tasks`
   - Click "Save and Continue"
   - Test users: Add your email address
   - Click "Save and Continue"

4. **Create OAuth Client ID**
   - Application type: "Desktop application"
   - Name: `Friday Day Management Client`
   - Click "Create"

5. **Download Credentials**
   - Click "Download JSON" for your new client ID
   - Save as `day_credentials.json` in your project directory

### Step 4: Install Dependencies

```bash
cd MCP_Servers/Day_Management_MCP
pip install -r requirements.txt
```

### Step 5: Configure Environment

1. **Move credentials file**
   ```bash
   # Move the downloaded file to your project directory
   mv ~/Downloads/client_secret_*.json /root/coding/Friday/MCP_Servers/Day_Management_MCP/day_credentials.json
   ```

2. **Update .env file**
   ```env
   # Add to your .env file
   GOOGLE_CREDENTIALS_PATH=MCP_Servers/Day_Management_MCP/day_credentials.json
   GOOGLE_TOKEN_PATH=MCP_Servers/Day_Management_MCP/day_token.pickle
   USER_TIMEZONE=America/New_York  # Change to your timezone
   ```

### Step 6: First-Time Authentication

1. **Run the Day Management MCP server**
   ```bash
   python MCP_Servers/Day_Management_MCP/day_management_mcp_server.py
   ```

2. **Complete OAuth Flow**
   - A browser window will open automatically
   - Sign in to your Google account
   - Grant permissions for Calendar and Tasks access
   - You'll see "The authentication flow has completed"

3. **Verify Authentication**
   - Check for `day_token.pickle` file creation
   - Server should start without errors

## 🔐 Required Scopes

The Day Management MCP server requires these Google API scopes:

- `https://www.googleapis.com/auth/calendar` - Full Calendar access (read/write)
- `https://www.googleapis.com/auth/tasks` - Full Tasks access (read/write)

## 📁 File Structure

After setup, your directory should look like:

```
MCP_Servers/Day_Management_MCP/
├── day_management_mcp_server.py
├── requirements.txt
├── day_credentials.json          # OAuth2 credentials (keep secure)
├── day_token.pickle             # Access token (auto-generated)
├── GOOGLE_OAUTH_SETUP.md        # This guide
└── day_management_server.log    # Server logs
```

## 🛠️ Troubleshooting

### Common Issues

#### **"day_credentials.json not found"**
- Ensure you downloaded the credentials file from Google Cloud Console
- Check the file path in your .env file
- Verify the file is in the correct directory

#### **"Access blocked: This app's request is invalid"**
- Make sure your OAuth consent screen is properly configured
- Add your email to test users list
- Check that Calendar and Tasks APIs are enabled

#### **"insufficient_scope" Error**
- Delete `day_token.pickle` file
- Restart the server to re-authenticate
- Make sure all required scopes are requested in OAuth consent screen

#### **Browser doesn't open for OAuth**
- Check your display settings if using SSH
- Use port forwarding: `ssh -L 8080:localhost:8080 user@host`
- Run authentication on local machine and copy `day_token.pickle`

#### **Timezone Issues**
- Set `USER_TIMEZONE` in .env file
- Use timezone names like "America/New_York", "Europe/London", "Asia/Tokyo"
- Check available timezones: `python -c "import pytz; print(pytz.all_timezones)"`

### Debug Mode

Enable detailed logging:

```python
# In day_management_mcp_server.py
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Best Practices

### Credential Management
- **Never commit day_credentials.json to version control**
- **Keep day_token.pickle secure** - it contains access tokens
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
# Google OAuth credentials
day_credentials.json
day_token.pickle
day_management_server.log
*.log
```

## 📊 API Limits

### Google Calendar API Quotas
- **Daily quota**: 1,000,000 requests per day
- **Per-user rate limit**: 100 requests per 100 seconds per user
- **Batch requests**: Up to 1000 operations per batch

### Google Tasks API Quotas
- **Daily quota**: 50,000 requests per day
- **Per-user rate limit**: 100 requests per 100 seconds per user

### Rate Limiting
The server implements automatic rate limiting and retry logic for API calls.

## 🧪 Testing Your Setup

### Quick Test Commands

```bash
# Test server startup
python day_management_mcp_server.py

# Test API access (from another terminal)
curl "http://127.0.0.1:5003/health"

# Test with Friday
python friday_with_memory.py
# Then ask: "What's on my calendar today?"
```

### Verification Checklist

- [ ] ✅ Google Cloud project created/selected
- [ ] ✅ Calendar API enabled
- [ ] ✅ Tasks API enabled
- [ ] ✅ OAuth2 credentials downloaded
- [ ] ✅ Dependencies installed
- [ ] ✅ First-time authentication completed
- [ ] ✅ day_token.pickle file created
- [ ] ✅ Server starts without errors
- [ ] ✅ Can retrieve calendar events through MCP
- [ ] ✅ Can retrieve tasks through MCP
- [ ] ✅ Can create events/tasks through MCP

## 🚀 Production Deployment

For production use:

1. **Use service account** instead of OAuth2
2. **Set up proper logging** and monitoring
3. **Implement rate limiting** in your application
4. **Use environment-specific credentials**
5. **Set up automated token refresh**

## 📚 Additional Resources

- **Google Calendar API Documentation**: https://developers.google.com/calendar/api
- **Google Tasks API Documentation**: https://developers.google.com/tasks/reference/rest
- **OAuth2 for Desktop Apps**: https://developers.google.com/identity/protocols/oauth2/native-app
- **Google Cloud Console**: https://console.cloud.google.com/
- **API Quotas & Limits**: https://developers.google.com/calendar/api/guides/quota

## 🆘 Support

If you encounter issues:

1. **Check the logs**: `day_management_server.log`
2. **Verify credentials**: Re-download from Google Cloud Console
3. **Test API access**: Use Google's API Explorer
4. **Check quotas**: Review usage in Google Cloud Console

## 📅 Calendar & Tasks Permissions

### What the Day Management MCP can do:

#### Calendar Permissions
- ✅ Read all calendar events
- ✅ Create new events
- ✅ Update existing events
- ✅ Delete events
- ✅ Manage event attendees
- ✅ Set event reminders

#### Tasks Permissions
- ✅ Read all task lists
- ✅ Read all tasks
- ✅ Create new tasks
- ✅ Update existing tasks
- ✅ Mark tasks as completed
- ✅ Set due dates
- ✅ Organize task hierarchy

### What it CANNOT do:
- ❌ Access other users' private calendars
- ❌ Modify calendar sharing settings
- ❌ Delete entire calendars
- ❌ Access deleted/archived items

Remember: Keep your credentials secure and never share them publicly!