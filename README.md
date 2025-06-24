# Friday AI Assistant

Friday is a smart AI assistant inspired by the character from The Avengers, designed to help with various tasks including email functionality.

## Setup

1. Install required dependencies:
```bash
pip install openai python-dotenv
```

2. Create a `.env` file in the project root with the following variables:
```
OPENAI_API_KEY=your_openai_api_key_here
GMAIL_USER=your_gmail_address@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
```

## Gmail Configuration

To use the email functionality, you need to:

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Use this app password in the `GMAIL_APP_PASSWORD` environment variable

## Usage

### Basic Usage
```python
from main import Friday

ai = Friday()
response = ai.get_response("Hello Friday!")
print(response)
```

### Email Function
The `send_email` function can be called directly:

```python
ai = Friday()
result = ai.send_email(
    to="recipient@example.com",
    subject="Test Email",
    body="This is a test email from Friday AI",
    attachment_path="/path/to/file.txt"  # Optional
)
print(result)
```

### Email Parameters
- `to` (required): Recipient email address
- `subject` (required): Email subject line
- `body` (required): Email body text
- `attachment_path` (optional): Full path to file attachment

### Available Tools
Friday has access to:
- DeepWiki MCP server for web search
- Email sending functionality via Gmail SMTP

## Running the Application

```bash
python main.py
```

The default configuration sends a test query asking about available tools.