#!/usr/bin/env python3
"""
Telegram MCP Server for Friday AI Assistant
Provides message retrieval and sending capabilities through Telegram Bot API
"""

import os
import sys
import time
import signal
import json
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

# FastMCP imports
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: FastMCP not installed. Install with: pip install fastmcp")
    sys.exit(1)

# Telegram Bot API imports
try:
    import requests
    from telegram import Bot, Update, Message
    from telegram.ext import Application, MessageHandler, filters, CommandHandler
except ImportError as e:
    print(f"Warning: python-telegram-bot import failed: {e}")
    print("Some features will be limited without Telegram bot integration")
    # Create dummy classes for testing
    class Bot: pass
    class Update: pass
    class Message: pass
    class Application:
        @staticmethod
        def builder(): 
            return type('Builder', (), {'token': lambda x: type('App', (), {'build': lambda: None})()})()
    class MessageHandler: 
        def __init__(self, *args, **kwargs): pass
    class filters:
        TEXT = None
        COMMAND = None
        PHOTO = None
    class CommandHandler:
        def __init__(self, *args, **kwargs): pass

# Environment variables
from dotenv import load_dotenv
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TelegramMessage:
    """Represents a Telegram message"""
    message_id: int
    chat_id: int
    chat_title: Optional[str]
    from_user: str
    from_user_id: int
    text: str
    timestamp: datetime
    reply_to_message_id: Optional[int] = None
    message_type: str = "text"

class TelegramMCPServer:
    """
    Telegram MCP Server for Friday AI Assistant
    Handles message retrieval and sending through Telegram Bot API
    """
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")  # Your personal chat ID
        self.bot = None
        self.application = None
        
        # Message cache for recent messages
        self.message_cache: List[TelegramMessage] = []
        self.cache_limit = 100
        
        # Initialize bot if token is available
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
        else:
            logger.warning("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    async def initialize_bot(self):
        """Initialize the Telegram bot application"""
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add message handler to cache incoming messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_incoming_message)
        )
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        
        logger.info("Telegram bot initialized successfully")
    
    async def _handle_incoming_message(self, update: Update, context) -> None:
        """Handle incoming messages and add to cache"""
        try:
            message = update.message
            if not message:
                return
            
            # Create TelegramMessage object
            telegram_msg = TelegramMessage(
                message_id=message.message_id,
                chat_id=message.chat_id,
                chat_title=message.chat.title or message.chat.first_name or "Private Chat",
                from_user=message.from_user.first_name or "Unknown",
                from_user_id=message.from_user.id,
                text=message.text or "",
                timestamp=message.date,
                reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
                message_type="text"
            )
            
            # Add to cache (keep only recent messages)
            self.message_cache.append(telegram_msg)
            if len(self.message_cache) > self.cache_limit:
                self.message_cache = self.message_cache[-self.cache_limit:]
            
            logger.info(f"Cached message from {telegram_msg.from_user}: {telegram_msg.text[:50]}...")
            
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")
    
    async def _handle_start(self, update: Update, context) -> None:
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 Friday AI Assistant Telegram Bot is now active!\n\n"
            "I can help you manage messages and automate responses.\n"
            "Use /help for available commands."
        )
    
    async def _handle_help(self, update: Update, context) -> None:
        """Handle /help command"""
        help_text = """
🤖 Friday AI Assistant - Telegram Bot

Available commands:
/start - Initialize the bot
/help - Show this help message

The bot automatically monitors and caches your messages for Friday to access.
Friday can retrieve recent messages and send replies on your behalf.
        """
        await update.message.reply_text(help_text)
    
    async def get_recent_messages(self, 
                                 limit: int = 20,
                                 hours_back: int = 24,
                                 chat_id: Optional[int] = None) -> List[Dict]:
        """
        Retrieve recent messages from cache or API
        
        Args:
            limit: Maximum number of messages to return
            hours_back: How many hours back to look
            chat_id: Specific chat ID to filter (optional)
        
        Returns:
            List of message dictionaries
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            # Filter messages by time and chat_id if specified
            filtered_messages = []
            for msg in self.message_cache:
                if msg.timestamp >= cutoff_time:
                    if chat_id is None or msg.chat_id == chat_id:
                        filtered_messages.append(msg)
            
            # Sort by timestamp (newest first) and limit
            filtered_messages.sort(key=lambda x: x.timestamp, reverse=True)
            filtered_messages = filtered_messages[:limit]
            
            # Convert to dictionaries for JSON serialization
            result = []
            for msg in filtered_messages:
                result.append({
                    "message_id": msg.message_id,
                    "chat_id": msg.chat_id,
                    "chat_title": msg.chat_title,
                    "from_user": msg.from_user,
                    "from_user_id": msg.from_user_id,
                    "text": msg.text,
                    "timestamp": msg.timestamp.isoformat(),
                    "reply_to_message_id": msg.reply_to_message_id,
                    "message_type": msg.message_type,
                    "relative_time": self._get_relative_time(msg.timestamp)
                })
            
            logger.info(f"Retrieved {len(result)} recent messages")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving recent messages: {e}")
            return []
    
    async def send_message(self, 
                          text: str,
                          chat_id: Optional[int] = None,
                          reply_to_message_id: Optional[int] = None,
                          parse_mode: Optional[str] = None) -> Dict:
        """
        Send a message through Telegram
        
        Args:
            text: Message text to send
            chat_id: Target chat ID (uses default if not specified)
            reply_to_message_id: Message ID to reply to (optional)
            parse_mode: Message formatting (Markdown, HTML, or None)
        
        Returns:
            Dictionary with send result
        """
        try:
            if not self.bot:
                return {"error": "Bot not initialized - missing TELEGRAM_BOT_TOKEN"}
            
            # Use provided chat_id or default
            target_chat_id = chat_id or self.chat_id
            if not target_chat_id:
                return {"error": "No chat_id specified and TELEGRAM_CHAT_ID not set"}
            
            # Send message
            message = await self.bot.send_message(
                chat_id=target_chat_id,
                text=text,
                reply_to_message_id=reply_to_message_id,
                parse_mode=parse_mode
            )
            
            logger.info(f"Message sent to chat {target_chat_id}: {text[:50]}...")
            
            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "text": message.text,
                "timestamp": message.date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"error": f"Failed to send message: {str(e)}"}
    
    async def get_chat_info(self) -> List[Dict]:
        """
        Get information about available chats
        
        Returns:
            List of chat information dictionaries
        """
        try:
            # Get unique chats from message cache
            chats = {}
            for msg in self.message_cache:
                if msg.chat_id not in chats:
                    chats[msg.chat_id] = {
                        "chat_id": msg.chat_id,
                        "chat_title": msg.chat_title,
                        "last_message_time": msg.timestamp,
                        "message_count": 1
                    }
                else:
                    chats[msg.chat_id]["message_count"] += 1
                    if msg.timestamp > chats[msg.chat_id]["last_message_time"]:
                        chats[msg.chat_id]["last_message_time"] = msg.timestamp
            
            # Convert to list and add relative times
            result = []
            for chat_info in chats.values():
                chat_info["last_message_time"] = chat_info["last_message_time"].isoformat()
                chat_info["relative_time"] = self._get_relative_time(
                    datetime.fromisoformat(chat_info["last_message_time"].replace('Z', '+00:00'))
                )
                result.append(chat_info)
            
            # Sort by last message time
            result.sort(key=lambda x: x["last_message_time"], reverse=True)
            
            logger.info(f"Retrieved information for {len(result)} chats")
            return result
            
        except Exception as e:
            logger.error(f"Error getting chat info: {e}")
            return []
    
    async def search_messages(self, 
                             query: str,
                             limit: int = 20,
                             hours_back: int = 168) -> List[Dict]:  # 168 hours = 1 week
        """
        Search messages by text content
        
        Args:
            query: Search query string
            limit: Maximum number of results
            hours_back: How many hours back to search
        
        Returns:
            List of matching message dictionaries
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            query_lower = query.lower()
            
            # Search through cached messages
            matching_messages = []
            for msg in self.message_cache:
                if (msg.timestamp >= cutoff_time and 
                    query_lower in msg.text.lower()):
                    matching_messages.append(msg)
            
            # Sort by relevance (exact matches first, then by recency)
            def relevance_score(msg):
                text_lower = msg.text.lower()
                exact_match = query_lower == text_lower
                starts_with = text_lower.startswith(query_lower)
                word_match = f" {query_lower} " in f" {text_lower} "
                
                # Score: exact match > starts with > word match > contains
                if exact_match:
                    return (4, msg.timestamp)
                elif starts_with:
                    return (3, msg.timestamp)
                elif word_match:
                    return (2, msg.timestamp)
                else:
                    return (1, msg.timestamp)
            
            matching_messages.sort(key=relevance_score, reverse=True)
            matching_messages = matching_messages[:limit]
            
            # Convert to dictionaries
            result = []
            for msg in matching_messages:
                result.append({
                    "message_id": msg.message_id,
                    "chat_id": msg.chat_id,
                    "chat_title": msg.chat_title,
                    "from_user": msg.from_user,
                    "from_user_id": msg.from_user_id,
                    "text": msg.text,
                    "timestamp": msg.timestamp.isoformat(),
                    "reply_to_message_id": msg.reply_to_message_id,
                    "message_type": msg.message_type,
                    "relative_time": self._get_relative_time(msg.timestamp)
                })
            
            logger.info(f"Found {len(result)} messages matching '{query}'")
            return result
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
    
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
    print("\nShutting down Telegram MCP server...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Initialize FastMCP server
mcp = FastMCP(
    name="telegram-mcp",
    host="127.0.0.1",
    port=5001,
    timeout=30
)

# Initialize Telegram server
telegram_server = TelegramMCPServer()

@mcp.tool()
async def get_recent_telegram_messages(limit: int = 20, 
                                      hours_back: int = 24,
                                      chat_id: int = None) -> str:
    """
    Retrieve recent Telegram messages.
    
    Parameters:
    - limit: Maximum number of messages to return (default: 20)
    - hours_back: How many hours back to look (default: 24)
    - chat_id: Specific chat ID to filter (optional)
    
    Returns:
    - Formatted string with recent messages
    """
    try:
        messages = await telegram_server.get_recent_messages(limit, hours_back, chat_id)
        
        if not messages:
            return f"No messages found in the last {hours_back} hours."
        
        # Format messages for display
        formatted_messages = []
        formatted_messages.append(f"📱 RECENT TELEGRAM MESSAGES (last {hours_back} hours)")
        formatted_messages.append("=" * 50)
        
        for msg in messages:
            time_str = msg["relative_time"]
            chat_info = f"[{msg['chat_title']}]" if msg['chat_title'] != "Private Chat" else "[DM]"
            
            formatted_messages.append(f"\n🕐 {time_str} - {chat_info}")
            formatted_messages.append(f"👤 {msg['from_user']}: {msg['text']}")
            
            if msg['reply_to_message_id']:
                formatted_messages.append(f"   ↳ Reply to message #{msg['reply_to_message_id']}")
        
        formatted_messages.append(f"\n📊 Total messages: {len(messages)}")
        
        return "\n".join(formatted_messages)
        
    except Exception as e:
        return f"Error retrieving messages: {str(e)}"

@mcp.tool()
async def send_telegram_message(text: str,
                               chat_id: int = None,
                               reply_to_message_id: int = None,
                               formatting: str = None) -> str:
    """
    Send a message through Telegram.
    
    Parameters:
    - text: Message text to send (required)
    - chat_id: Target chat ID (uses default if not specified)
    - reply_to_message_id: Message ID to reply to (optional)
    - formatting: Message formatting - 'Markdown', 'HTML', or None (optional)
    
    Returns:
    - Result of the send operation
    """
    try:
        result = await telegram_server.send_message(
            text=text,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            parse_mode=formatting
        )
        
        if result.get("success"):
            return f"✅ Message sent successfully to chat {result['chat_id']} (Message ID: {result['message_id']})"
        else:
            return f"❌ Failed to send message: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error sending message: {str(e)}"

@mcp.tool()
async def search_telegram_messages(query: str,
                                  limit: int = 20,
                                  hours_back: int = 168) -> str:
    """
    Search Telegram messages by text content.
    
    Parameters:
    - query: Search query string (required)
    - limit: Maximum number of results (default: 20)
    - hours_back: How many hours back to search (default: 168 = 1 week)
    
    Returns:
    - Formatted string with search results
    """
    try:
        messages = await telegram_server.search_messages(query, limit, hours_back)
        
        if not messages:
            return f"No messages found containing '{query}' in the last {hours_back} hours."
        
        # Format search results
        formatted_results = []
        formatted_results.append(f"🔍 TELEGRAM MESSAGE SEARCH RESULTS")
        formatted_results.append(f"Query: '{query}' | Found: {len(messages)} messages")
        formatted_results.append("=" * 50)
        
        for msg in messages:
            time_str = msg["relative_time"]
            chat_info = f"[{msg['chat_title']}]" if msg['chat_title'] != "Private Chat" else "[DM]"
            
            # Highlight the query in the text
            highlighted_text = msg['text']
            if query.lower() in highlighted_text.lower():
                # Simple highlighting (could be enhanced)
                highlighted_text = highlighted_text.replace(
                    query, f"**{query}**"
                ).replace(
                    query.lower(), f"**{query.lower()}**"
                ).replace(
                    query.upper(), f"**{query.upper()}**"
                )
            
            formatted_results.append(f"\n🕐 {time_str} - {chat_info}")
            formatted_results.append(f"👤 {msg['from_user']}: {highlighted_text}")
            formatted_results.append(f"   📍 Message ID: {msg['message_id']}")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching messages: {str(e)}"

@mcp.tool()
async def get_telegram_chats() -> str:
    """
    Get information about available Telegram chats.
    
    Returns:
    - Formatted string with chat information
    """
    try:
        chats = await telegram_server.get_chat_info()
        
        if not chats:
            return "No chat information available. Send some messages to populate the cache."
        
        # Format chat information
        formatted_chats = []
        formatted_chats.append("💬 AVAILABLE TELEGRAM CHATS")
        formatted_chats.append("=" * 40)
        
        for chat in chats:
            chat_type = "Group" if chat['chat_title'] != "Private Chat" else "Direct Message"
            formatted_chats.append(f"\n📍 Chat ID: {chat['chat_id']}")
            formatted_chats.append(f"   📝 Title: {chat['chat_title']}")
            formatted_chats.append(f"   📋 Type: {chat_type}")
            formatted_chats.append(f"   📊 Messages: {chat['message_count']}")
            formatted_chats.append(f"   🕐 Last activity: {chat['relative_time']}")
        
        formatted_chats.append(f"\n📊 Total chats: {len(chats)}")
        
        return "\n".join(formatted_chats)
        
    except Exception as e:
        return f"Error retrieving chat information: {str(e)}"

async def start_telegram_bot():
    """Start the Telegram bot in the background"""
    try:
        await telegram_server.initialize_bot()
        
        # Start polling in the background
        if telegram_server.application:
            await telegram_server.application.initialize()
            await telegram_server.application.start()
            await telegram_server.application.updater.start_polling()
            logger.info("Telegram bot started and polling for messages")
        
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")

async def main():
    """Main function to run the MCP server"""
    try:
        print("Starting Telegram MCP server on 127.0.0.1:5001")
        
        # Start Telegram bot if token is available
        if telegram_server.bot_token:
            # Start bot polling in background task
            asyncio.create_task(start_telegram_bot())
            print("Telegram bot started and listening for messages")
        else:
            print("Warning: TELEGRAM_BOT_TOKEN not found - message monitoring disabled")
        
        # Start MCP server
        await mcp.run()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())