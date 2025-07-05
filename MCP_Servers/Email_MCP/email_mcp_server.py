#!/usr/bin/env python3
"""
Email Management MCP Server for Friday AI Assistant
Provides comprehensive email management capabilities through Gmail API
"""

import os
import sys
import json
import time
import signal
import base64
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes

# FastMCP imports
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: FastMCP not installed. Install with: pip install fastmcp")
    sys.exit(1)

# Gmail API imports
try:
    import pickle
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Warning: Google API libraries import failed: {e}")
    print("Install with: pip install google-api-python-client google-auth google-auth-oauthlib")
    sys.exit(1)

# Environment variables
from dotenv import load_dotenv
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

@dataclass
class EmailMessage:
    """Represents an email message"""
    message_id: str
    thread_id: str
    from_email: str
    from_name: str
    to_emails: List[str]
    cc_emails: List[str]
    bcc_emails: List[str]
    subject: str
    body_text: str
    body_html: str
    timestamp: datetime
    is_read: bool
    is_starred: bool
    labels: List[str]
    attachments: List[Dict[str, Any]]
    snippet: str

class EmailMCPServer:
    """
    Email Management MCP Server for Friday AI Assistant
    Handles comprehensive email operations through Gmail API
    """
    
    def __init__(self):
        self.credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "token.pickle")
        self.service = None
        self.credentials = None
        
        # Initialize Gmail API service
        try:
            self.service = self._get_gmail_service()
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            self.service = None
    
    def _get_gmail_service(self):
        """Initialize Gmail API service with authentication"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {self.credentials_path}\n"
                        "Please download from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        return build('gmail', 'v1', credentials=creds)
    
    def _parse_email_message(self, message_data: Dict) -> EmailMessage:
        """Parse Gmail API message data into EmailMessage object"""
        try:
            headers = message_data['payload'].get('headers', [])
            header_dict = {h['name'].lower(): h['value'] for h in headers}
            
            # Extract basic info
            message_id = message_data['id']
            thread_id = message_data['threadId']
            subject = header_dict.get('subject', '(No Subject)')
            from_header = header_dict.get('from', '')
            to_header = header_dict.get('to', '')
            cc_header = header_dict.get('cc', '')
            bcc_header = header_dict.get('bcc', '')
            
            # Parse from email
            from_email = from_header.split('<')[-1].replace('>', '').strip()
            from_name = from_header.split('<')[0].strip().strip('"')
            
            # Parse recipient emails
            to_emails = [email.strip() for email in to_header.split(',') if email.strip()]
            cc_emails = [email.strip() for email in cc_header.split(',') if email.strip()]
            bcc_emails = [email.strip() for email in bcc_header.split(',') if email.strip()]
            
            # Get timestamp
            timestamp = datetime.fromtimestamp(int(message_data['internalDate']) / 1000)
            
            # Get labels and read status
            labels = message_data.get('labelIds', [])
            is_read = 'UNREAD' not in labels
            is_starred = 'STARRED' in labels
            
            # Get body content
            body_text, body_html = self._extract_body_content(message_data['payload'])
            
            # Get attachments
            attachments = self._extract_attachments(message_data['payload'])
            
            # Get snippet
            snippet = message_data.get('snippet', '')
            
            return EmailMessage(
                message_id=message_id,
                thread_id=thread_id,
                from_email=from_email,
                from_name=from_name,
                to_emails=to_emails,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                timestamp=timestamp,
                is_read=is_read,
                is_starred=is_starred,
                labels=labels,
                attachments=attachments,
                snippet=snippet
            )
            
        except Exception as e:
            logger.error(f"Error parsing email message: {e}")
            raise
    
    def _extract_body_content(self, payload: Dict) -> tuple:
        """Extract text and HTML body content from email payload"""
        body_text = ""
        body_html = ""
        
        def extract_from_part(part):
            nonlocal body_text, body_html
            
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_text += base64.urlsafe_b64decode(data).decode('utf-8')
            elif part.get('mimeType') == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_html += base64.urlsafe_b64decode(data).decode('utf-8')
            elif part.get('parts'):
                for subpart in part['parts']:
                    extract_from_part(subpart)
        
        extract_from_part(payload)
        return body_text, body_html
    
    def _extract_attachments(self, payload: Dict) -> List[Dict]:
        """Extract attachment information from email payload"""
        attachments = []
        
        def extract_from_part(part):
            if part.get('filename'):
                attachment_id = part.get('body', {}).get('attachmentId')
                if attachment_id:
                    attachments.append({
                        'filename': part['filename'],
                        'attachment_id': attachment_id,
                        'mime_type': part.get('mimeType', ''),
                        'size': part.get('body', {}).get('size', 0)
                    })
            elif part.get('parts'):
                for subpart in part['parts']:
                    extract_from_part(subpart)
        
        extract_from_part(payload)
        return attachments
    
    async def get_recent_emails(self, 
                               limit: int = 20,
                               hours_back: int = 24,
                               unread_only: bool = False,
                               label_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Get recent emails from Gmail
        
        Args:
            limit: Maximum number of emails to return
            hours_back: How many hours back to look
            unread_only: Only return unread emails
            label_ids: Filter by specific labels
        
        Returns:
            List of email dictionaries
        """
        try:
            if not self.service:
                return []
            
            # Build query
            query_parts = []
            
            # Time filter
            since_time = datetime.now() - timedelta(hours=hours_back)
            query_parts.append(f"after:{since_time.strftime('%Y/%m/%d')}")
            
            # Unread filter
            if unread_only:
                query_parts.append("is:unread")
            
            # Label filter
            if label_ids:
                for label_id in label_ids:
                    query_parts.append(f"label:{label_id}")
            
            query = " ".join(query_parts)
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get full message details
            email_list = []
            for message in messages:
                try:
                    msg_data = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    email_obj = self._parse_email_message(msg_data)
                    email_list.append(self._email_to_dict(email_obj))
                    
                except Exception as e:
                    logger.error(f"Error processing message {message['id']}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(email_list)} emails")
            return email_list
            
        except Exception as e:
            logger.error(f"Error retrieving recent emails: {e}")
            return []
    
    async def search_emails(self, 
                           query: str,
                           limit: int = 20,
                           hours_back: int = 168) -> List[Dict]:  # 1 week default
        """
        Search emails by query
        
        Args:
            query: Search query
            limit: Maximum number of results
            hours_back: How many hours back to search
        
        Returns:
            List of matching email dictionaries
        """
        try:
            if not self.service:
                return []
            
            # Build search query
            since_time = datetime.now() - timedelta(hours=hours_back)
            full_query = f"{query} after:{since_time.strftime('%Y/%m/%d')}"
            
            # Search emails
            results = self.service.users().messages().list(
                userId='me',
                q=full_query,
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get full message details
            email_list = []
            for message in messages:
                try:
                    msg_data = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    email_obj = self._parse_email_message(msg_data)
                    email_list.append(self._email_to_dict(email_obj))
                    
                except Exception as e:
                    logger.error(f"Error processing search result {message['id']}: {e}")
                    continue
            
            logger.info(f"Found {len(email_list)} emails matching '{query}'")
            return email_list
            
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
    
    async def get_email_by_id(self, message_id: str) -> Optional[Dict]:
        """
        Get a specific email by message ID
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Email dictionary or None
        """
        try:
            if not self.service:
                return None
            
            msg_data = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            email_obj = self._parse_email_message(msg_data)
            return self._email_to_dict(email_obj)
            
        except Exception as e:
            logger.error(f"Error retrieving email {message_id}: {e}")
            return None
    
    async def send_email(self, 
                        to: str,
                        subject: str,
                        body: str,
                        cc: Optional[str] = None,
                        bcc: Optional[str] = None,
                        html_body: Optional[str] = None,
                        attachment_paths: Optional[List[str]] = None) -> Dict:
        """
        Send an email through Gmail API
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (text)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html_body: HTML version of email body
            attachment_paths: List of file paths to attach
        
        Returns:
            Send result dictionary
        """
        try:
            if not self.service:
                return {"error": "Gmail service not initialized"}
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc
            
            # Add body parts
            if body:
                msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments
            if attachment_paths:
                for file_path in attachment_paths:
                    if os.path.exists(file_path):
                        self._add_attachment(msg, file_path)
            
            # Send email
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully to {to}")
            return {
                "success": True,
                "message_id": send_result['id'],
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"error": f"Failed to send email: {str(e)}"}
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add file attachment to email message"""
        try:
            with open(file_path, "rb") as attachment:
                # Guess content type
                content_type, encoding = mimetypes.guess_type(file_path)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                
                main_type, sub_type = content_type.split('/', 1)
                
                if main_type == 'text':
                    part = MIMEText(attachment.read().decode(), _subtype=sub_type)
                else:
                    part = MIMEBase(main_type, sub_type)
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{os.path.basename(file_path)}"'
                )
                msg.attach(part)
                
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {e}")
    
    async def mark_as_read(self, message_ids: List[str]) -> Dict:
        """Mark emails as read"""
        try:
            if not self.service:
                return {"error": "Gmail service not initialized"}
            
            result = self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            
            logger.info(f"Marked {len(message_ids)} emails as read")
            return {"success": True, "processed": len(message_ids)}
            
        except Exception as e:
            logger.error(f"Error marking emails as read: {e}")
            return {"error": str(e)}
    
    async def mark_as_unread(self, message_ids: List[str]) -> Dict:
        """Mark emails as unread"""
        try:
            if not self.service:
                return {"error": "Gmail service not initialized"}
            
            result = self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'addLabelIds': ['UNREAD']
                }
            ).execute()
            
            logger.info(f"Marked {len(message_ids)} emails as unread")
            return {"success": True, "processed": len(message_ids)}
            
        except Exception as e:
            logger.error(f"Error marking emails as unread: {e}")
            return {"error": str(e)}
    
    async def archive_emails(self, message_ids: List[str]) -> Dict:
        """Archive emails (remove from inbox)"""
        try:
            if not self.service:
                return {"error": "Gmail service not initialized"}
            
            result = self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'removeLabelIds': ['INBOX']
                }
            ).execute()
            
            logger.info(f"Archived {len(message_ids)} emails")
            return {"success": True, "processed": len(message_ids)}
            
        except Exception as e:
            logger.error(f"Error archiving emails: {e}")
            return {"error": str(e)}
    
    async def delete_emails(self, message_ids: List[str]) -> Dict:
        """Delete emails (move to trash)"""
        try:
            if not self.service:
                return {"error": "Gmail service not initialized"}
            
            result = self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'addLabelIds': ['TRASH']
                }
            ).execute()
            
            logger.info(f"Deleted {len(message_ids)} emails")
            return {"success": True, "processed": len(message_ids)}
            
        except Exception as e:
            logger.error(f"Error deleting emails: {e}")
            return {"error": str(e)}
    
    async def get_labels(self) -> List[Dict]:
        """Get all Gmail labels"""
        try:
            if not self.service:
                return []
            
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            return [{"id": label['id'], "name": label['name']} for label in labels]
            
        except Exception as e:
            logger.error(f"Error retrieving labels: {e}")
            return []
    
    def _email_to_dict(self, email: EmailMessage) -> Dict:
        """Convert EmailMessage object to dictionary"""
        return {
            "message_id": email.message_id,
            "thread_id": email.thread_id,
            "from_email": email.from_email,
            "from_name": email.from_name,
            "to_emails": email.to_emails,
            "cc_emails": email.cc_emails,
            "bcc_emails": email.bcc_emails,
            "subject": email.subject,
            "body_text": email.body_text,
            "body_html": email.body_html,
            "timestamp": email.timestamp.isoformat(),
            "is_read": email.is_read,
            "is_starred": email.is_starred,
            "labels": email.labels,
            "attachments": email.attachments,
            "snippet": email.snippet,
            "relative_time": self._get_relative_time(email.timestamp)
        }
    
    def _get_relative_time(self, timestamp: datetime) -> str:
        """Get human-readable relative time"""
        now = datetime.now()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=None)
        if now.tzinfo is None:
            now = now.replace(tzinfo=None)
        
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print("\nShutting down Email MCP server...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Initialize FastMCP server
mcp = FastMCP(
    name="email-mcp",
    host="127.0.0.1",
    port=5002,
    timeout=30
)

# Initialize Email server
email_server = EmailMCPServer()

@mcp.tool()
async def get_recent_emails(limit: int = 20, 
                           hours_back: int = 24,
                           unread_only: bool = False) -> str:
    """
    Get recent emails from Gmail inbox.
    
    Parameters:
    - limit: Maximum number of emails to return (default: 20)
    - hours_back: How many hours back to look (default: 24)
    - unread_only: Only return unread emails (default: False)
    
    Returns:
    - Formatted string with recent emails
    """
    try:
        emails = await email_server.get_recent_emails(limit, hours_back, unread_only)
        
        if not emails:
            return f"No emails found in the last {hours_back} hours."
        
        # Format emails for display
        formatted_emails = []
        formatted_emails.append(f"📧 RECENT EMAILS (last {hours_back} hours)")
        formatted_emails.append("=" * 50)
        
        for email in emails:
            status = "📩 UNREAD" if not email['is_read'] else "📧 READ"
            star = "⭐" if email['is_starred'] else ""
            
            formatted_emails.append(f"\n{status} {star}")
            formatted_emails.append(f"🕐 {email['relative_time']}")
            formatted_emails.append(f"👤 From: {email['from_name']} <{email['from_email']}>")
            formatted_emails.append(f"📝 Subject: {email['subject']}")
            formatted_emails.append(f"💬 Preview: {email['snippet'][:100]}...")
            formatted_emails.append(f"🆔 ID: {email['message_id']}")
        
        formatted_emails.append(f"\n📊 Total emails: {len(emails)}")
        
        return "\n".join(formatted_emails)
        
    except Exception as e:
        return f"Error retrieving emails: {str(e)}"

@mcp.tool()
async def search_emails(query: str,
                       limit: int = 20,
                       hours_back: int = 168) -> str:
    """
    Search emails by query.
    
    Parameters:
    - query: Search query (required)
    - limit: Maximum number of results (default: 20)
    - hours_back: How many hours back to search (default: 168 = 1 week)
    
    Returns:
    - Formatted string with search results
    """
    try:
        emails = await email_server.search_emails(query, limit, hours_back)
        
        if not emails:
            return f"No emails found matching '{query}' in the last {hours_back} hours."
        
        # Format search results
        formatted_results = []
        formatted_results.append(f"🔍 EMAIL SEARCH RESULTS")
        formatted_results.append(f"Query: '{query}' | Found: {len(emails)} emails")
        formatted_results.append("=" * 50)
        
        for email in emails:
            status = "📩 UNREAD" if not email['is_read'] else "📧 READ"
            star = "⭐" if email['is_starred'] else ""
            
            formatted_results.append(f"\n{status} {star}")
            formatted_results.append(f"🕐 {email['relative_time']}")
            formatted_results.append(f"👤 From: {email['from_name']} <{email['from_email']}>")
            formatted_results.append(f"📝 Subject: {email['subject']}")
            formatted_results.append(f"💬 Preview: {email['snippet'][:100]}...")
            formatted_results.append(f"🆔 ID: {email['message_id']}")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching emails: {str(e)}"

@mcp.tool()
async def read_email(message_id: str) -> str:
    """
    Read a specific email by message ID.
    
    Parameters:
    - message_id: Gmail message ID (required)
    
    Returns:
    - Formatted string with full email content
    """
    try:
        email = await email_server.get_email_by_id(message_id)
        
        if not email:
            return f"Email with ID '{message_id}' not found."
        
        # Format full email
        formatted_email = []
        formatted_email.append(f"📧 EMAIL DETAILS")
        formatted_email.append("=" * 50)
        formatted_email.append(f"🆔 Message ID: {email['message_id']}")
        formatted_email.append(f"👤 From: {email['from_name']} <{email['from_email']}>")
        formatted_email.append(f"📮 To: {', '.join(email['to_emails'])}")
        
        if email['cc_emails']:
            formatted_email.append(f"📋 CC: {', '.join(email['cc_emails'])}")
        
        formatted_email.append(f"📝 Subject: {email['subject']}")
        formatted_email.append(f"🕐 Date: {email['timestamp']}")
        formatted_email.append(f"📊 Status: {'UNREAD' if not email['is_read'] else 'READ'}")
        
        if email['attachments']:
            formatted_email.append(f"📎 Attachments: {len(email['attachments'])}")
            for att in email['attachments']:
                formatted_email.append(f"   • {att['filename']} ({att['size']} bytes)")
        
        formatted_email.append("\n" + "=" * 50)
        formatted_email.append("📄 CONTENT:")
        formatted_email.append(email['body_text'] or email['body_html'][:1000] + "...")
        
        return "\n".join(formatted_email)
        
    except Exception as e:
        return f"Error reading email: {str(e)}"

@mcp.tool()
async def send_email(to: str,
                    subject: str,
                    body: str,
                    cc: str = None,
                    bcc: str = None,
                    html_body: str = None) -> str:
    """
    Send an email through Gmail.
    
    Parameters:
    - to: Recipient email address (required)
    - subject: Email subject (required)
    - body: Email body text (required)
    - cc: CC recipients (optional)
    - bcc: BCC recipients (optional)
    - html_body: HTML version of email body (optional)
    
    Returns:
    - Result of the send operation
    """
    try:
        result = await email_server.send_email(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            html_body=html_body
        )
        
        if result.get("success"):
            return f"✅ Email sent successfully to {result['to']} (Message ID: {result['message_id']})"
        else:
            return f"❌ Failed to send email: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error sending email: {str(e)}"

@mcp.tool()
async def mark_emails_as_read(message_ids: str) -> str:
    """
    Mark emails as read.
    
    Parameters:
    - message_ids: Comma-separated list of message IDs (required)
    
    Returns:
    - Result of the mark operation
    """
    try:
        ids = [mid.strip() for mid in message_ids.split(',')]
        result = await email_server.mark_as_read(ids)
        
        if result.get("success"):
            return f"✅ Marked {result['processed']} emails as read"
        else:
            return f"❌ Failed to mark emails as read: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error marking emails as read: {str(e)}"

@mcp.tool()
async def archive_emails(message_ids: str) -> str:
    """
    Archive emails (remove from inbox).
    
    Parameters:
    - message_ids: Comma-separated list of message IDs (required)
    
    Returns:
    - Result of the archive operation
    """
    try:
        ids = [mid.strip() for mid in message_ids.split(',')]
        result = await email_server.archive_emails(ids)
        
        if result.get("success"):
            return f"✅ Archived {result['processed']} emails"
        else:
            return f"❌ Failed to archive emails: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error archiving emails: {str(e)}"

@mcp.tool()
async def get_gmail_labels() -> str:
    """
    Get all Gmail labels.
    
    Returns:
    - Formatted string with all labels
    """
    try:
        labels = await email_server.get_labels()
        
        if not labels:
            return "No labels found."
        
        # Format labels
        formatted_labels = []
        formatted_labels.append("🏷️ GMAIL LABELS")
        formatted_labels.append("=" * 30)
        
        for label in labels:
            formatted_labels.append(f"• {label['name']} (ID: {label['id']})")
        
        formatted_labels.append(f"\n📊 Total labels: {len(labels)}")
        
        return "\n".join(formatted_labels)
        
    except Exception as e:
        return f"Error retrieving labels: {str(e)}"

async def main():
    """Main function to run the MCP server"""
    try:
        print("Starting Email MCP server on 127.0.0.1:5002")
        
        # Check if Gmail service is available
        if email_server.service:
            print("Gmail API service initialized successfully")
        else:
            print("Warning: Gmail API service not initialized - some features will be limited")
        
        # Start MCP server
        await mcp.run()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())