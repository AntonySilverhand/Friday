#!/usr/bin/env python3
"""
Simple Gmail MCP Server compatible with OpenAI API
"""
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/root/coding/Jarvis/MCP_Servers/Gmail_MCP/Gmail-mcp-server/gmail-mcp-server/.env')

app = Flask(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email(recipient: str, subject: str, body: str, attachment_path: str = None) -> dict:
    """Send an email using Gmail SMTP."""
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
            msg.attach(part)
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, recipient, msg.as_string())
        server.quit()
        
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}

@app.route('/mcp', methods=['GET'])
def get_tools():
    """Return available tools for MCP."""
    tools = {
        "tools": [
            {
                "name": "send_email",
                "description": "Send an email via Gmail SMTP",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient": {
                            "type": "string",
                            "description": "Email address to send to"
                        },
                        "subject": {
                            "type": "string", 
                            "description": "Email subject"
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body text"
                        },
                        "attachment_path": {
                            "type": "string",
                            "description": "Optional file path for attachment"
                        }
                    },
                    "required": ["recipient", "subject", "body"]
                }
            }
        ]
    }
    return jsonify(tools)

@app.route('/mcp/send_email', methods=['POST'])
def send_email_endpoint():
    """Execute send_email tool."""
    try:
        data = request.get_json()
        recipient = data.get('recipient')
        subject = data.get('subject')
        body = data.get('body')
        attachment_path = data.get('attachment_path')
        
        result = send_email(recipient, subject, body, attachment_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    print(f"Starting Simple Gmail MCP Server on 127.0.0.1:5000")
    print(f"SMTP Username: {SMTP_USERNAME}")
    app.run(host="127.0.0.1", port=5000, debug=False)