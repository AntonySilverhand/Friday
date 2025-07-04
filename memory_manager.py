#!/usr/bin/env python3
"""
Memory Manager for Friday AI Assistant
Handles timeline-based conversation storage and retrieval using SQLite
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import threading
import os

@dataclass
class ConversationEntry:
    """Represents a single conversation entry in the timeline"""
    id: str
    timestamp: datetime
    conversation_id: str
    role: str  # 'user', 'assistant', 'system'
    message_content: str
    tool_calls: Optional[Dict] = None
    tool_results: Optional[Dict] = None
    sequence_number: int = 0

@dataclass
class ConversationSession:
    """Represents a conversation session grouping related interactions"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    title: Optional[str] = None
    summary: Optional[str] = None

@dataclass
class ToolUsageEntry:
    """Represents a tool usage entry in the timeline"""
    id: str
    timestamp: datetime
    conversation_id: str
    tool_name: str
    parameters: Dict
    result: Any
    execution_time: float

class MemoryManager:
    """
    Manages timeline-based conversation storage and retrieval for Friday AI
    """
    
    def __init__(self, db_path: str = "friday_memory.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    tool_calls TEXT,
                    tool_results TEXT,
                    sequence_number INTEGER NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversation_sessions(session_id)
                )
            ''')
            
            # Create conversation_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    title TEXT,
                    summary TEXT
                )
            ''')
            
            # Create tool_usage_log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tool_usage_log (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    conversation_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    result TEXT,
                    execution_time REAL NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversation_sessions(session_id)
                )
            ''')
            
            # Create indexes for efficient timeline queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_usage_timestamp ON tool_usage_log(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_usage_conversation_id ON tool_usage_log(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON conversation_sessions(start_time)')
            
            conn.commit()
    
    def create_conversation_session(self, title: Optional[str] = None) -> str:
        """Create a new conversation session and return its ID"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_sessions (session_id, start_time, title)
                VALUES (?, ?, ?)
            ''', (session_id, now, title))
            conn.commit()
        
        return session_id
    
    def end_conversation_session(self, session_id: str, summary: Optional[str] = None):
        """End a conversation session with optional summary"""
        now = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversation_sessions 
                SET end_time = ?, summary = ?
                WHERE session_id = ?
            ''', (now, summary, session_id))
            conn.commit()
    
    def store_conversation(self, conversation_entry: ConversationEntry) -> str:
        """Store a conversation entry in the timeline"""
        entry_id = conversation_entry.id or str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations 
                (id, timestamp, conversation_id, role, message_content, tool_calls, tool_results, sequence_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id,
                conversation_entry.timestamp,
                conversation_entry.conversation_id,
                conversation_entry.role,
                conversation_entry.message_content,
                json.dumps(conversation_entry.tool_calls) if conversation_entry.tool_calls else None,
                json.dumps(conversation_entry.tool_results) if conversation_entry.tool_results else None,
                conversation_entry.sequence_number
            ))
            conn.commit()
        
        return entry_id
    
    def store_tool_usage(self, tool_entry: ToolUsageEntry) -> str:
        """Store a tool usage entry in the timeline"""
        entry_id = tool_entry.id or str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tool_usage_log 
                (id, timestamp, conversation_id, tool_name, parameters, result, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id,
                tool_entry.timestamp,
                tool_entry.conversation_id,
                tool_entry.tool_name,
                json.dumps(tool_entry.parameters),
                json.dumps(tool_entry.result) if tool_entry.result is not None else None,
                tool_entry.execution_time
            ))
            conn.commit()
        
        return entry_id
    
    def retrieve_history(self, 
                        conversation_id: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: Optional[int] = None,
                        keywords: Optional[List[str]] = None,
                        tool_name: Optional[str] = None,
                        role_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve conversation history with flexible filtering options
        
        Args:
            conversation_id: Filter by specific conversation
            start_time: Filter from this time onwards
            end_time: Filter up to this time
            limit: Maximum number of entries to return
            keywords: Search for these keywords in message content
            tool_name: Filter by specific tool usage
            role_filter: Filter by role (user/assistant/system)
        
        Returns:
            List of conversation entries with timeline context
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build base query
            query = '''
                SELECT c.*, cs.title as session_title, cs.summary as session_summary
                FROM conversations c
                LEFT JOIN conversation_sessions cs ON c.conversation_id = cs.session_id
                WHERE 1=1
            '''
            params = []
            
            # Add filters
            if conversation_id:
                query += ' AND c.conversation_id = ?'
                params.append(conversation_id)
            
            if start_time:
                query += ' AND c.timestamp >= ?'
                params.append(start_time)
            
            if end_time:
                query += ' AND c.timestamp <= ?'
                params.append(end_time)
            
            if keywords:
                for keyword in keywords:
                    query += ' AND c.message_content LIKE ?'
                    params.append(f'%{keyword}%')
            
            if role_filter:
                query += ' AND c.role = ?'
                params.append(role_filter)
            
            # Add tool usage filter if specified
            if tool_name:
                query += ''' AND c.conversation_id IN (
                    SELECT DISTINCT conversation_id FROM tool_usage_log WHERE tool_name = ?
                )'''
                params.append(tool_name)
            
            # Order by timeline
            query += ' ORDER BY c.timestamp ASC, c.sequence_number ASC'
            
            # Add limit
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries and parse JSON fields
            results = []
            for row in rows:
                entry = dict(row)
                # Parse JSON fields
                if entry['tool_calls']:
                    entry['tool_calls'] = json.loads(entry['tool_calls'])
                if entry['tool_results']:
                    entry['tool_results'] = json.loads(entry['tool_results'])
                results.append(entry)
            
            return results
    
    def get_recent_context(self, hours: int = 24, limit: int = 50) -> List[Dict]:
        """Get recent conversation context for relevance analysis"""
        since = datetime.now() - timedelta(hours=hours)
        return self.retrieve_history(start_time=since, limit=limit)
    
    def search_by_timeframe(self, 
                          timeframe: str, 
                          timeframe_value: int,
                          limit: Optional[int] = None) -> List[Dict]:
        """
        Search conversations by timeframe
        
        Args:
            timeframe: 'hours', 'days', 'weeks', 'months'
            timeframe_value: Number of timeframe units to look back
            limit: Maximum results to return
        """
        now = datetime.now()
        
        if timeframe == 'hours':
            start_time = now - timedelta(hours=timeframe_value)
        elif timeframe == 'days':
            start_time = now - timedelta(days=timeframe_value)
        elif timeframe == 'weeks':
            start_time = now - timedelta(weeks=timeframe_value)
        elif timeframe == 'months':
            start_time = now - timedelta(days=timeframe_value * 30)  # Approximate
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        return self.retrieve_history(start_time=start_time, limit=limit)
    
    def get_tool_usage_timeline(self, 
                              tool_name: Optional[str] = None,
                              start_time: Optional[datetime] = None,
                              limit: Optional[int] = None) -> List[Dict]:
        """Get timeline of tool usage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM tool_usage_log WHERE 1=1'
            params = []
            
            if tool_name:
                query += ' AND tool_name = ?'
                params.append(tool_name)
            
            if start_time:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            query += ' ORDER BY timestamp ASC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries and parse JSON fields
            results = []
            for row in rows:
                entry = dict(row)
                entry['parameters'] = json.loads(entry['parameters'])
                if entry['result']:
                    entry['result'] = json.loads(entry['result'])
                results.append(entry)
            
            return results
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict]:
        """Get summary of a specific conversation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute('''
                SELECT * FROM conversation_sessions WHERE session_id = ?
            ''', (conversation_id,))
            session = cursor.fetchone()
            
            if not session:
                return None
            
            # Get conversation stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_messages,
                    MIN(timestamp) as first_message,
                    MAX(timestamp) as last_message,
                    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages
                FROM conversations 
                WHERE conversation_id = ?
            ''', (conversation_id,))
            stats = cursor.fetchone()
            
            # Get tool usage stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as tool_calls,
                    COUNT(DISTINCT tool_name) as unique_tools
                FROM tool_usage_log 
                WHERE conversation_id = ?
            ''', (conversation_id,))
            tool_stats = cursor.fetchone()
            
            return {
                'session': dict(session),
                'stats': dict(stats),
                'tool_stats': dict(tool_stats)
            }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old conversation data beyond specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete old conversations
            cursor.execute('DELETE FROM conversations WHERE timestamp < ?', (cutoff_date,))
            
            # Delete old tool usage logs
            cursor.execute('DELETE FROM tool_usage_log WHERE timestamp < ?', (cutoff_date,))
            
            # Delete old sessions that have no conversations
            cursor.execute('''
                DELETE FROM conversation_sessions 
                WHERE session_id NOT IN (
                    SELECT DISTINCT conversation_id FROM conversations
                )
            ''')
            
            conn.commit()
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the memory database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM conversations')
            total_conversations = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM conversation_sessions')
            total_sessions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM tool_usage_log')
            total_tool_usage = cursor.fetchone()[0]
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'total_conversations': total_conversations,
                'total_sessions': total_sessions,
                'total_tool_usage': total_tool_usage,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2)
            }