#!/usr/bin/env python3
"""
Enhanced Friday AI Assistant with Timeline-Based Memory Management
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
import smtplib
import time
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, List, Any

# Import our memory management modules
from memory_manager import MemoryManager, ConversationEntry, ToolUsageEntry
from relevance_detector import RelevanceDetector, create_relevance_detector
from history_retrieval import (
    HistoryRetrieval, 
    create_retrieve_history_function,
    create_search_tool_usage_function,
    create_get_recent_context_function
)

load_dotenv()

class EnhancedFriday:
    """
    Enhanced Friday AI Assistant with timeline-based memory management
    """
    
    def __init__(self, memory_db_path: str = "friday_memory.db"):
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize memory management components
        self.memory_manager = MemoryManager(memory_db_path)
        self.relevance_detector = create_relevance_detector(self.memory_manager, self.client)
        self.history_retrieval = HistoryRetrieval(self.memory_manager)
        
        # Current conversation session
        self.current_session_id: Optional[str] = None
        self.message_sequence = 0
        
        # Base system prompt for Friday
        self.base_system_prompt = """You are Friday from the movie The Avengers, a smart high-tech AI assistant developed by Iron Man, now you are assisting Antony, me. You speak in a brief, clean, high efficient way. You are assistive. You use a very formal tone, for most of the time you call me sir.

IMPORTANT: You start each conversation fresh unless relevant context is provided above. You have access to functions to retrieve conversation history when needed. Use them when you need to understand past interactions, actions taken, or ongoing tasks."""
        
        # Initialize function registry for tool calls
        self._function_registry = {}
        self._setup_function_registry()
    
    def _setup_function_registry(self):
        """Setup the function registry for tool calls"""
        # Email function
        self._function_registry["send_email"] = self.send_email
        
        # History retrieval functions
        self._function_registry["retrieve_history"] = self.history_retrieval.retrieve_history
        self._function_registry["search_tool_usage"] = self.history_retrieval.search_tool_usage
        self._function_registry["get_recent_context"] = self.history_retrieval.get_recent_context
    
    def start_conversation_session(self, title: Optional[str] = None) -> str:
        """Start a new conversation session"""
        self.current_session_id = self.memory_manager.create_conversation_session(title)
        self.message_sequence = 0
        return self.current_session_id
    
    def end_conversation_session(self, summary: Optional[str] = None):
        """End the current conversation session"""
        if self.current_session_id:
            self.memory_manager.end_conversation_session(self.current_session_id, summary)
            self.current_session_id = None
            self.message_sequence = 0
    
    def get_response(self, input_text: str, force_context: bool = False) -> str:
        """
        Get a response from Friday with smart context injection
        
        Args:
            input_text: User's message
            force_context: Force inclusion of recent context (bypass relevance detection)
        
        Returns:
            Friday's response
        """
        try:
            # Ensure we have a conversation session
            if not self.current_session_id:
                self.start_conversation_session()
            
            # Store user message first
            self._store_conversation_entry(
                role="user",
                message=input_text,
                sequence=self.message_sequence
            )
            self.message_sequence += 1
            
            # Determine if context should be included
            context_to_inject = None
            
            if force_context:
                # Force recent context
                context_to_inject = self.history_retrieval.get_recent_context(hours=24, limit=20)
            else:
                # Use relevance detection
                relevance_decision = self.relevance_detector.analyze_relevance(input_text)
                
                if relevance_decision.is_relevant and relevance_decision.confidence > 0.6:
                    context_to_inject = self.relevance_detector.get_relevant_context(relevance_decision)
            
            # Build the input for Friday
            friday_input = self._build_friday_input(input_text, context_to_inject)
            
            # Get response from Friday
            start_time = time.time()
            response = self.client.responses.create(
                model="gpt-4.1-mini",
                tools=self._get_tools_config(),
                input=friday_input
            )
            execution_time = time.time() - start_time
            
            # Extract response text and tool calls
            response_text = response.output_text or ""
            tool_calls = getattr(response, 'tool_calls', None)
            tool_results = {}
            
            # Execute tool calls if present
            if tool_calls:
                tool_results = self._execute_tool_calls(tool_calls)
                
                # If tools were called, get a follow-up response with results
                if tool_results:
                    follow_up_input = self._build_tool_followup_input(friday_input, tool_calls, tool_results)
                    follow_up_response = self.client.responses.create(
                        model="gpt-4.1-mini",
                        input=follow_up_input
                    )
                    response_text = follow_up_response.output_text or response_text
            
            # Store Friday's response
            self._store_conversation_entry(
                role="assistant",
                message=response_text,
                tool_calls=tool_calls,
                tool_results=tool_results,
                sequence=self.message_sequence
            )
            self.message_sequence += 1
            
            return response_text
            
        except Exception as e:
            error_message = f"I apologize, sir. An error occurred: {str(e)}"
            
            # Store error response
            try:
                self._store_conversation_entry(
                    role="assistant",
                    message=error_message,
                    sequence=self.message_sequence
                )
                self.message_sequence += 1
            except:
                pass  # Don't let storage errors compound the issue
            
            return error_message
    
    def _build_friday_input(self, user_message: str, context: Optional[str] = None) -> List[Dict]:
        """Build the input for Friday including context if relevant"""
        messages = []
        
        # System message with context if provided
        system_content = self.base_system_prompt
        if context:
            system_content = f"{context}\n\n{self.base_system_prompt}"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # User message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _build_tool_followup_input(self, original_input: List[Dict], tool_calls: List, tool_results: Dict) -> List[Dict]:
        """Build input for follow-up response after tool execution"""
        messages = original_input.copy()
        
        # Add tool calls and results to the conversation
        tool_summary = []
        for call in tool_calls:
            tool_name = call.get('name', 'unknown')
            result = tool_results.get(tool_name, 'No result')
            tool_summary.append(f"Tool '{tool_name}' executed with result: {result}")
        
        messages.append({
            "role": "system",
            "content": f"Tool execution results:\n" + "\n".join(tool_summary)
        })
        
        return messages
    
    def _get_tools_config(self) -> List[Dict]:
        """Get the tools configuration for Friday"""
        return [
            # DeepWiki MCP server
            {
                "type": "mcp",
                "server_label": "deepwiki",
                "server_url": "https://mcp.deepwiki.com/mcp",
                "require_approval": "never",
            },
            # Telegram MCP server
            {
                "type": "mcp",
                "server_label": "telegram",
                "server_url": "http://127.0.0.1:5001/mcp",
                "require_approval": "never",
            },
            # Send email function
            {
                "type": "function",
                "name": "send_email",
                "description": "Send an email to a given recipient with a subject and body via Gmail SMTP",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
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
                    "required": ["to", "subject", "body"],
                    "additional_properties": False
                }
            },
            # History retrieval function
            {
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
                        }
                    },
                    "required": [],
                    "additional_properties": False
                }
            },
            # Search tool usage function
            {
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
                }
            },
            # Get recent context function
            {
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
                }
            }
        ]
    
    def _execute_tool_calls(self, tool_calls: List) -> Dict[str, Any]:
        """Execute tool calls and return results"""
        results = {}
        
        for call in tool_calls:
            tool_name = call.get('name')
            parameters = call.get('parameters', {})
            
            if tool_name in self._function_registry:
                try:
                    start_time = time.time()
                    result = self._function_registry[tool_name](**parameters)
                    execution_time = time.time() - start_time
                    
                    results[tool_name] = result
                    
                    # Store tool usage in timeline
                    if self.current_session_id:
                        tool_entry = ToolUsageEntry(
                            id=str(uuid.uuid4()),
                            timestamp=datetime.now(),
                            conversation_id=self.current_session_id,
                            tool_name=tool_name,
                            parameters=parameters,
                            result=result,
                            execution_time=execution_time
                        )
                        self.memory_manager.store_tool_usage(tool_entry)
                    
                except Exception as e:
                    results[tool_name] = f"Error executing {tool_name}: {str(e)}"
            else:
                results[tool_name] = f"Unknown tool: {tool_name}"
        
        return results
    
    def _store_conversation_entry(self, 
                                 role: str, 
                                 message: str, 
                                 tool_calls: Optional[List] = None,
                                 tool_results: Optional[Dict] = None,
                                 sequence: int = 0):
        """Store a conversation entry in the timeline"""
        if not self.current_session_id:
            return
        
        entry = ConversationEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            conversation_id=self.current_session_id,
            role=role,
            message_content=message,
            tool_calls=tool_calls,
            tool_results=tool_results,
            sequence_number=sequence
        )
        
        self.memory_manager.store_conversation(entry)
    
    def send_email(self, to: str, subject: str, body: str, attachment_path: Optional[str] = None) -> str:
        """Send an email via Gmail SMTP"""
        try:
            gmail_user = os.getenv("GMAIL_USER")
            gmail_password = os.getenv("GMAIL_APP_PASSWORD")
            
            if not gmail_user or not gmail_password:
                return "Error: Gmail credentials not found in environment variables"
            
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = to
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_password)
            text = msg.as_string()
            server.sendmail(gmail_user, to, text)
            server.quit()
            
            return f"Email sent successfully to {to}"
            
        except Exception as e:
            return f"Error sending email: {str(e)}"
    
    def get_memory_stats(self) -> Dict:
        """Get memory database statistics"""
        return self.memory_manager.get_database_stats()
    
    def cleanup_old_memory(self, days_to_keep: int = 30):
        """Clean up old memory data"""
        self.memory_manager.cleanup_old_data(days_to_keep)

def main():
    """Example usage of Enhanced Friday"""
    # Initialize Friday with memory
    friday = EnhancedFriday()
    
    try:
        # Start a conversation session
        session_id = friday.start_conversation_session("Test Session")
        print(f"Started conversation session: {session_id}")
        
        # Test basic interaction
        print("\n=== Test 1: Basic Interaction ===")
        response1 = friday.get_response("Hello Friday, what can you help me with?")
        print(f"Friday: {response1}")
        
        # Test memory retrieval
        print("\n=== Test 2: Memory Retrieval ===")
        response2 = friday.get_response("What tools do you have available?")
        print(f"Friday: {response2}")
        
        # Test context awareness
        print("\n=== Test 3: Context Awareness ===")
        response3 = friday.get_response("What did we discuss earlier?")
        print(f"Friday: {response3}")
        
        # End session
        friday.end_conversation_session("Test session completed")
        
        # Display memory stats
        print("\n=== Memory Statistics ===")
        stats = friday.get_memory_stats()
        print(f"Memory Stats: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()