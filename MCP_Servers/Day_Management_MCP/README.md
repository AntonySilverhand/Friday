# Day Management MCP Server for Friday AI Assistant

This MCP (Model Context Protocol) server provides comprehensive day management capabilities for Friday AI Assistant through Google Calendar and Google Tasks APIs, enabling intelligent scheduling, task management, and day planning.

## 🚀 Features

### 📅 Calendar Management
- **Event Access**: Read and retrieve calendar events
- **Event Creation**: Create new events with smart scheduling
- **Event Modification**: Update existing events (time, location, attendees)
- **Event Deletion**: Remove events from calendar
- **Conflict Detection**: Smart scheduling to avoid conflicts
- **Free Time Analysis**: Calculate available time slots

### 📋 Task Management
- **Task Lists**: Access and manage multiple task lists
- **Task Operations**: Create, update, complete, and organize tasks
- **Due Date Management**: Set and track task deadlines
- **Overdue Detection**: Identify and prioritize overdue tasks
- **Task Hierarchy**: Support for subtasks and task organization

### 🗓️ Intelligent Day Planning
- **Day Overview**: Comprehensive daily schedule with events and tasks
- **Free Time Optimization**: Identify optimal time slots for new activities
- **Smart Scheduling**: AI-powered scheduling recommendations
- **Timeline Integration**: Works with Friday's memory system for context

### 🔍 Advanced Capabilities
- **Natural Language Parsing**: Flexible date/time input formats
- **Timezone Support**: Proper timezone handling and conversion
- **Batch Operations**: Efficient handling of multiple operations
- **Rich Formatting**: AI-friendly presentation of calendar data

## 🛠️ MCP Tools Available

### `get_calendar_events`
Get upcoming calendar events.
- **Parameters**: `days_ahead` (int), `max_results` (int)
- **Returns**: Formatted timeline of events with details and free time slots

### `create_calendar_event`
Create a new calendar event.
- **Parameters**: `title` (required), `start_datetime` (required), `end_datetime` (required), `description`, `location`, `attendees`
- **Returns**: Event creation confirmation with calendar link

### `update_calendar_event`
Update an existing calendar event.
- **Parameters**: `event_id` (required), `title`, `start_datetime`, `end_datetime`, `description`, `location`
- **Returns**: Update confirmation with new details

### `delete_calendar_event`
Delete a calendar event.
- **Parameters**: `event_id` (required)
- **Returns**: Deletion confirmation

### `get_tasks`
Get tasks from task lists.
- **Parameters**: `tasklist_id`, `show_completed` (bool), `max_results` (int)
- **Returns**: Organized task list with status, due dates, and priorities

### `create_task`
Create a new task.
- **Parameters**: `title` (required), `notes`, `due_date`, `tasklist_id`
- **Returns**: Task creation confirmation

### `update_task`
Update an existing task.
- **Parameters**: `task_id` (required), `title`, `notes`, `due_date`, `status`, `tasklist_id`
- **Returns**: Update confirmation

### `complete_task`
Mark a task as completed.
- **Parameters**: `task_id` (required), `tasklist_id`
- **Returns**: Completion confirmation

### `get_day_overview`
Get comprehensive day overview.
- **Parameters**: `target_date` (optional, defaults to today)
- **Returns**: Integrated view of events, tasks, and free time for the day

### `get_tasklists`
Get all available task lists.
- **Returns**: List of task lists with metadata

## 📋 Setup Instructions

### Step 1: Google Cloud Setup
1. **Create/Select Google Cloud Project**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing

2. **Enable Required APIs**
   - Enable "Google Calendar API"
   - Enable "Google Tasks API"

3. **Create OAuth2 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Create OAuth client ID for Desktop application
   - Download credentials as `day_credentials.json`

### Step 2: Local Setup
1. **Install Dependencies**
   ```bash
   cd MCP_Servers/Day_Management_MCP
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Add to .env file
   GOOGLE_CREDENTIALS_PATH=MCP_Servers/Day_Management_MCP/day_credentials.json
   GOOGLE_TOKEN_PATH=MCP_Servers/Day_Management_MCP/day_token.pickle
   USER_TIMEZONE=America/New_York  # Your timezone
   ```

3. **Place Credentials**
   ```bash
   mv ~/Downloads/client_secret_*.json MCP_Servers/Day_Management_MCP/day_credentials.json
   ```

### Step 3: First-Time Authentication
1. **Start Day Management MCP Server**
   ```bash
   python MCP_Servers/Day_Management_MCP/day_management_mcp_server.py
   ```

2. **Complete OAuth Flow**
   - Browser opens automatically
   - Sign in and grant Calendar + Tasks permissions
   - `day_token.pickle` created automatically

### Step 4: Integration with Friday
The Day Management MCP is already integrated in Friday's configuration:
```python
{
    "type": "mcp",
    "server_label": "day-management",
    "server_url": "http://127.0.0.1:5003/mcp",
    "require_approval": "never",
}
```

## 💡 Usage Examples

### Calendar Operations
```python
# Get upcoming events
response = friday.get_response("What's on my calendar for the next 3 days?")

# Create a meeting
response = friday.get_response("Schedule a team meeting tomorrow at 2 PM for 1 hour in Conference Room A")

# Update an event
response = friday.get_response("Move my 3 PM meeting to 4 PM tomorrow")

# Check for conflicts
response = friday.get_response("Can I schedule a 30-minute call at 11 AM tomorrow?")
```

### Task Management
```python
# Get current tasks
response = friday.get_response("Show me my pending tasks")

# Create a task
response = friday.get_response("Add a task to review the quarterly report due next Friday")

# Complete a task
response = friday.get_response("Mark the project presentation task as completed")

# Check overdue items
response = friday.get_response("What tasks are overdue?")
```

### Day Planning
```python
# Daily overview
response = friday.get_response("Give me an overview of my day today")

# Find free time
response = friday.get_response("When do I have 2 hours free this week for focused work?")

# Plan tomorrow
response = friday.get_response("Help me plan tomorrow's schedule")

# Optimize schedule
response = friday.get_response("What's the best time for a 1-hour client call this week?")
```

### Smart Scheduling
```python
# Context-aware scheduling
response = friday.get_response("Schedule a follow-up meeting with the client from today's 2 PM meeting")

# Batch operations
response = friday.get_response("Move all my Friday afternoon meetings to next week")

# Travel time consideration
response = friday.get_response("Schedule lunch with Sarah, considering I have a meeting downtown at 2 PM")
```

## 🔐 Security & Authentication

### OAuth2 Scopes Required
- `https://www.googleapis.com/auth/calendar` - Full Calendar access
- `https://www.googleapis.com/auth/tasks` - Full Tasks access

### Credential Security
- **day_credentials.json**: OAuth2 client credentials (keep secure)
- **day_token.pickle**: Access/refresh tokens (auto-managed)
- **Environment variables**: Secure path configuration

### Best Practices
- Never commit credentials to version control
- Use environment-specific credential files
- Monitor API usage in Google Cloud Console
- Set up proper .gitignore entries

## 🔧 Configuration

### Server Settings
```python
# In day_management_mcp_server.py
mcp = FastMCP(
    name="day-management-mcp",
    host="127.0.0.1",
    port=5003,
    timeout=30
)
```

### Timezone Configuration
```env
# Supported timezone examples
USER_TIMEZONE=America/New_York
USER_TIMEZONE=Europe/London
USER_TIMEZONE=Asia/Tokyo
USER_TIMEZONE=UTC
```

### File Paths
```env
GOOGLE_CREDENTIALS_PATH=MCP_Servers/Day_Management_MCP/day_credentials.json
GOOGLE_TOKEN_PATH=MCP_Servers/Day_Management_MCP/day_token.pickle
```

## 🧪 Testing

### Run Integration Tests
```bash
python test_day_management_integration.py
```

### Test Components
- Environment setup verification
- Google API library imports
- OAuth credentials validation
- Timezone configuration
- Date parsing functionality
- Day Management server creation
- MCP tools registration
- Friday integration check

### Expected Results
- 100% pass rate for code structure tests
- OAuth flow completion
- Server startup without errors
- Calendar and Tasks API access

## 🐛 Troubleshooting

### Common Issues

#### **"day_credentials.json not found"**
- Download from Google Cloud Console
- Check file path in .env
- Verify file permissions

#### **OAuth Flow Fails**
- Check OAuth consent screen configuration
- Add your email to test users
- Ensure Calendar + Tasks APIs are enabled

#### **"insufficient_scope" Error**
- Delete day_token.pickle
- Restart server to re-authenticate
- Verify all scopes in OAuth consent screen

#### **Timezone Issues**
- Set valid USER_TIMEZONE in .env
- Use standard timezone names
- Check `pytz.all_timezones` for valid options

#### **Date Parsing Errors**
- Use ISO format: "2024-07-05T14:30:00"
- Natural language: "tomorrow at 2 PM"
- Relative dates: "next Monday 9am"

### Debug Commands
```bash
# Check credentials format
python -c "import json; print(json.load(open('day_credentials.json'))['installed'].keys())"

# Test timezone
python -c "import pytz; print(pytz.timezone('America/New_York'))"

# Verify server health
curl "http://127.0.0.1:5003/health"
```

## 📊 API Limits & Performance

### Google Calendar API Quotas
- **Daily quota**: 1,000,000 requests/day
- **Per-user rate**: 100 requests/100 seconds
- **Batch operations**: Up to 1000 per batch

### Google Tasks API Quotas
- **Daily quota**: 50,000 requests/day
- **Per-user rate**: 100 requests/100 seconds

### Performance Optimization
- Automatic retry with exponential backoff
- Batch processing for multiple operations
- Efficient event/task parsing and caching
- Smart query optimization

## 🔄 Integration with Friday's Memory

### Timeline Awareness
- Events and tasks stored in Friday's memory timeline
- Context-aware scheduling based on conversation history
- Smart suggestions based on past scheduling patterns

### Memory-Enhanced Features
- **Pattern Recognition**: Learn scheduling preferences
- **Context Carryover**: Reference previous meetings/tasks
- **Intelligent Suggestions**: Propose optimal meeting times
- **Historical Analysis**: Track productivity patterns

## 🌟 Advanced Features

### Smart Scheduling
- **Conflict Detection**: Automatically identify scheduling conflicts
- **Travel Time**: Consider location and travel between meetings
- **Preference Learning**: Adapt to user scheduling preferences
- **Optimal Timing**: Suggest best times based on calendar patterns

### Day Optimization
- **Free Time Analysis**: Identify productive time blocks
- **Task Scheduling**: Automatically schedule tasks in free slots
- **Meeting Clustering**: Group related meetings efficiently
- **Buffer Time**: Add appropriate buffers between activities

### Natural Language Processing
- **Flexible Input**: Accept various date/time formats
- **Context Understanding**: Interpret relative references
- **Smart Defaults**: Apply intelligent defaults for incomplete information
- **Ambiguity Resolution**: Ask clarifying questions when needed

## 🚀 Future Enhancements

### Planned Features
- **Meeting Room Management**: Integration with room booking systems
- **Team Coordination**: Multi-calendar scheduling across team members
- **Smart Reminders**: AI-powered reminder optimization
- **Productivity Analytics**: Track and analyze time usage patterns
- **External Integrations**: Connect with other productivity tools

### AI Enhancements
- **Predictive Scheduling**: Suggest schedule optimizations
- **Habit Formation**: Support routine building and habit tracking
- **Priority Intelligence**: Auto-prioritize tasks based on context
- **Workload Balancing**: Prevent overcommitment and burnout

## 📚 Resources

- **Google Calendar API Documentation**: https://developers.google.com/calendar/api
- **Google Tasks API Documentation**: https://developers.google.com/tasks/reference/rest
- **OAuth2 Guide**: https://developers.google.com/identity/protocols/oauth2
- **Google Cloud Console**: https://console.cloud.google.com/
- **Timezone Reference**: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## 📄 License

This Day Management MCP server is part of the Friday AI Assistant project and follows the same licensing terms.

---

**🎉 With this Day Management MCP, Friday becomes your intelligent personal assistant for managing your entire day - from calendar events to task completion, with smart scheduling and optimization capabilities!**

## 📋 Quick Reference

### Server Ports
- **Telegram MCP**: 127.0.0.1:5001
- **Email MCP**: 127.0.0.1:5002  
- **Day Management MCP**: 127.0.0.1:5003

### Required Files
- `day_credentials.json` - OAuth2 credentials from Google Cloud
- `day_token.pickle` - Auto-generated access tokens
- `.env` - Environment configuration

### Key Commands
```bash
# Start server
python MCP_Servers/Day_Management_MCP/day_management_mcp_server.py

# Run tests
python test_day_management_integration.py

# Check health
curl http://127.0.0.1:5003/health
```