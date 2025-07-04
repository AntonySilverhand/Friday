#!/usr/bin/env python3
"""
History Retrieval Functions for Friday AI Assistant
Provides function calling interface for accessing timeline-based conversation history
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from memory_manager import MemoryManager

class HistoryRetrieval:
    """
    Provides history retrieval functions for Friday AI Assistant
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    def retrieve_history(self, 
                        timeframe: Optional[str] = None,
                        timeframe_value: Optional[int] = None,
                        limit: Optional[int] = 50,
                        keywords: Optional[str] = None,
                        tool_name: Optional[str] = None,
                        role_filter: Optional[str] = None,
                        conversation_id: Optional[str] = None) -> str:
        """
        Retrieve conversation history with flexible filtering options.
        
        Args:
            timeframe: Time period to search - 'hours', 'days', 'weeks', 'months'
            timeframe_value: Number of timeframe units to look back
            limit: Maximum number of entries to return (default: 50)
            keywords: Comma-separated keywords to search for in messages
            tool_name: Filter by specific tool usage (e.g., 'send_email')
            role_filter: Filter by role - 'user', 'assistant', or 'system'
            conversation_id: Filter by specific conversation session
        
        Returns:
            Formatted string containing the conversation history timeline
        """
        try:
            # Parse keywords if provided
            keyword_list = None
            if keywords:
                keyword_list = [k.strip() for k in keywords.split(',')]
            
            # Calculate time range if timeframe is specified
            start_time = None
            if timeframe and timeframe_value:
                now = datetime.now()
                if timeframe == 'hours':
                    start_time = now - timedelta(hours=timeframe_value)
                elif timeframe == 'days':
                    start_time = now - timedelta(days=timeframe_value)
                elif timeframe == 'weeks':
                    start_time = now - timedelta(weeks=timeframe_value)
                elif timeframe == 'months':
                    start_time = now - timedelta(days=timeframe_value * 30)
                else:
                    return f"Error: Invalid timeframe '{timeframe}'. Valid options: hours, days, weeks, months"
            
            # Retrieve history
            history = self.memory_manager.retrieve_history(
                conversation_id=conversation_id,
                start_time=start_time,
                limit=limit,
                keywords=keyword_list,
                tool_name=tool_name,
                role_filter=role_filter
            )
            
            if not history:
                return "No conversation history found matching the specified criteria."
            
            # Format the timeline response
            return self._format_timeline(history, timeframe, timeframe_value)
            
        except Exception as e:
            return f"Error retrieving history: {str(e)}"
    
    def get_recent_context(self, hours: int = 24, limit: int = 20) -> str:
        """
        Get recent conversation context for understanding current situation.
        
        Args:
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of entries (default: 20)
        
        Returns:
            Formatted string with recent conversation context
        """
        try:
            context = self.memory_manager.get_recent_context(hours=hours, limit=limit)
            
            if not context:
                return f"No conversation history found in the last {hours} hours."
            
            return self._format_context(context, hours)
            
        except Exception as e:
            return f"Error retrieving recent context: {str(e)}"
    
    def search_tool_usage(self, 
                         tool_name: Optional[str] = None,
                         timeframe: Optional[str] = None,
                         timeframe_value: Optional[int] = None,
                         limit: Optional[int] = 20) -> str:
        """
        Search for tool usage in the timeline.
        
        Args:
            tool_name: Specific tool to search for (e.g., 'send_email')
            timeframe: Time period - 'hours', 'days', 'weeks', 'months'
            timeframe_value: Number of timeframe units to look back
            limit: Maximum number of entries (default: 20)
        
        Returns:
            Formatted string with tool usage timeline
        """
        try:
            # Calculate time range if specified
            start_time = None
            if timeframe and timeframe_value:
                now = datetime.now()
                if timeframe == 'hours':
                    start_time = now - timedelta(hours=timeframe_value)
                elif timeframe == 'days':
                    start_time = now - timedelta(days=timeframe_value)
                elif timeframe == 'weeks':
                    start_time = now - timedelta(weeks=timeframe_value)
                elif timeframe == 'months':
                    start_time = now - timedelta(days=timeframe_value * 30)
                else:
                    return f"Error: Invalid timeframe '{timeframe}'"
            
            # Get tool usage timeline
            tool_usage = self.memory_manager.get_tool_usage_timeline(
                tool_name=tool_name,
                start_time=start_time,
                limit=limit
            )
            
            if not tool_usage:
                tool_filter = f" for tool '{tool_name}'" if tool_name else ""
                time_filter = f" in the last {timeframe_value} {timeframe}" if timeframe else ""
                return f"No tool usage found{tool_filter}{time_filter}."
            
            return self._format_tool_usage(tool_usage, tool_name, timeframe, timeframe_value)
            
        except Exception as e:
            return f"Error searching tool usage: {str(e)}"
    
    def get_conversation_summary(self, conversation_id: str) -> str:
        """
        Get a summary of a specific conversation session.
        
        Args:
            conversation_id: The conversation session ID to summarize
        
        Returns:
            Formatted string with conversation summary
        """
        try:
            summary = self.memory_manager.get_conversation_summary(conversation_id)
            
            if not summary:
                return f"No conversation found with ID: {conversation_id}"
            
            return self._format_conversation_summary(summary)
            
        except Exception as e:
            return f"Error getting conversation summary: {str(e)}"
    
    def _format_timeline(self, history: List[Dict], timeframe: Optional[str], timeframe_value: Optional[int]) -> str:
        """Format conversation history into a readable timeline"""
        if not history:
            return "No conversation history found."
        
        # Header
        time_desc = f"last {timeframe_value} {timeframe}" if timeframe else "matching criteria"
        output = [f"📅 CONVERSATION TIMELINE ({time_desc})", "=" * 50]
        
        current_date = None
        for entry in history:
            # Parse timestamp
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            entry_date = timestamp.strftime('%Y-%m-%d')
            
            # Add date header if new date
            if current_date != entry_date:
                current_date = entry_date
                output.append(f"\n📅 {timestamp.strftime('%B %d, %Y (%A)')}")
                output.append("-" * 30)
            
            # Format time
            time_str = timestamp.strftime('%H:%M:%S')
            
            # Format role
            role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(entry['role'], "❓")
            
            # Format message
            message = entry['message_content'].strip()
            if len(message) > 200:
                message = message[:200] + "..."
            
            output.append(f"{time_str} {role_icon} {entry['role'].upper()}: {message}")
            
            # Add tool information if present
            if entry.get('tool_calls'):
                tools = entry['tool_calls']
                if isinstance(tools, dict):
                    output.append(f"    🔧 Used tools: {', '.join(tools.keys())}")
                elif isinstance(tools, list):
                    tool_names = [tool.get('name', 'unknown') for tool in tools]
                    output.append(f"    🔧 Used tools: {', '.join(tool_names)}")
            
            if entry.get('tool_results'):
                output.append(f"    ✅ Tool results available")
        
        output.append(f"\n📊 Total entries: {len(history)}")
        return "\n".join(output)
    
    def _format_context(self, context: List[Dict], hours: int) -> str:
        """Format recent context for relevance analysis"""
        if not context:
            return f"No recent activity in the last {hours} hours."
        
        output = [f"🕐 RECENT CONTEXT (last {hours} hours)", "=" * 40]
        
        for entry in context[-10:]:  # Show last 10 entries
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            time_str = timestamp.strftime('%H:%M')
            
            role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(entry['role'], "❓")
            
            message = entry['message_content'].strip()
            if len(message) > 150:
                message = message[:150] + "..."
            
            output.append(f"{time_str} {role_icon} {message}")
        
        return "\n".join(output)
    
    def _format_tool_usage(self, tool_usage: List[Dict], tool_name: Optional[str], 
                          timeframe: Optional[str], timeframe_value: Optional[int]) -> str:
        """Format tool usage timeline"""
        if not tool_usage:
            return "No tool usage found."
        
        # Header
        tool_desc = f"for {tool_name}" if tool_name else "all tools"
        time_desc = f"last {timeframe_value} {timeframe}" if timeframe else "matching criteria"
        output = [f"🔧 TOOL USAGE TIMELINE ({tool_desc} - {time_desc})", "=" * 50]
        
        for entry in tool_usage:
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            exec_time = entry.get('execution_time', 0)
            params = entry.get('parameters', {})
            result = entry.get('result')
            
            output.append(f"{time_str} - {entry['tool_name']}")
            output.append(f"    ⏱️  Execution time: {exec_time:.2f}s")
            
            if params:
                param_str = ', '.join([f"{k}={v}" for k, v in params.items() if k != 'attachment_path'])
                if param_str:
                    output.append(f"    📝 Parameters: {param_str}")
            
            if result:
                result_str = str(result)
                if len(result_str) > 100:
                    result_str = result_str[:100] + "..."
                output.append(f"    ✅ Result: {result_str}")
            
            output.append("")
        
        output.append(f"📊 Total tool calls: {len(tool_usage)}")
        return "\n".join(output)
    
    def _format_conversation_summary(self, summary: Dict) -> str:
        """Format conversation summary"""
        session = summary['session']
        stats = summary['stats']
        tool_stats = summary['tool_stats']
        
        output = [f"📋 CONVERSATION SUMMARY", "=" * 30]
        output.append(f"Session ID: {session['session_id']}")
        
        if session.get('title'):
            output.append(f"Title: {session['title']}")
        
        # Time information
        start_time = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
        output.append(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if session.get('end_time'):
            end_time = datetime.fromisoformat(session['end_time'].replace('Z', '+00:00'))
            output.append(f"Ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            duration = end_time - start_time
            output.append(f"Duration: {duration}")
        
        # Statistics
        output.append(f"\n📊 Statistics:")
        output.append(f"  Total messages: {stats['total_messages']}")
        output.append(f"  User messages: {stats['user_messages']}")
        output.append(f"  Assistant messages: {stats['assistant_messages']}")
        output.append(f"  Tool calls: {tool_stats['tool_calls']}")
        output.append(f"  Unique tools used: {tool_stats['unique_tools']}")
        
        if session.get('summary'):
            output.append(f"\n📝 Summary: {session['summary']}")
        
        return "\n".join(output)

# Function call interface for Friday AI
def create_retrieve_history_function(memory_manager: MemoryManager):
    """
    Create the retrieve_history function definition for Friday's tool set
    """
    history_retrieval = HistoryRetrieval(memory_manager)
    
    return {
        "type": "function",
        "name": "retrieve_history",
        "description": "Retrieve conversation history and timeline information. Use this to understand what happened in previous conversations, what tools were used, and their results.",
        "parameters": {
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["hours", "days", "weeks", "months"],
                    "description": "Time period to search back"
                },
                "timeframe_value": {
                    "type": "integer",
                    "description": "Number of timeframe units to look back (e.g., 2 for '2 days')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of entries to return (default: 50)"
                },
                "keywords": {
                    "type": "string",
                    "description": "Comma-separated keywords to search for in messages"
                },
                "tool_name": {
                    "type": "string",
                    "description": "Filter by specific tool usage (e.g., 'send_email')"
                },
                "role_filter": {
                    "type": "string",
                    "enum": ["user", "assistant", "system"],
                    "description": "Filter by role"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Filter by specific conversation session ID"
                }
            },
            "required": [],
            "additional_properties": False
        },
        "function": history_retrieval.retrieve_history
    }

def create_search_tool_usage_function(memory_manager: MemoryManager):
    """
    Create the search_tool_usage function definition for Friday's tool set
    """
    history_retrieval = HistoryRetrieval(memory_manager)
    
    return {
        "type": "function",
        "name": "search_tool_usage",
        "description": "Search for tool usage in the timeline to understand what actions were taken and their results.",
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Specific tool to search for (e.g., 'send_email')"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["hours", "days", "weeks", "months"],
                    "description": "Time period to search back"
                },
                "timeframe_value": {
                    "type": "integer",
                    "description": "Number of timeframe units to look back"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of entries to return (default: 20)"
                }
            },
            "required": [],
            "additional_properties": False
        },
        "function": history_retrieval.search_tool_usage
    }

def create_get_recent_context_function(memory_manager: MemoryManager):
    """
    Create the get_recent_context function definition for Friday's tool set
    """
    history_retrieval = HistoryRetrieval(memory_manager)
    
    return {
        "type": "function",
        "name": "get_recent_context",
        "description": "Get recent conversation context to understand the current situation and ongoing tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "Number of hours to look back (default: 24)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of entries to return (default: 20)"
                }
            },
            "required": [],
            "additional_properties": False
        },
        "function": history_retrieval.get_recent_context
    }