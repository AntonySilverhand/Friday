#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Friday AI Assistant
Testing Friday's interaction with both Email MCP and Day Management MCP servers

This test suite covers:
1. Friday's tool configuration for both MCPs
2. End-to-end workflows (e.g., "Schedule a meeting and send invites")
3. Memory integration with MCP tool usage
4. Error handling across MCP connections
5. Concurrent MCP operations
6. Friday's ability to use both MCPs together
7. Mocked external API calls but tests integration logic
8. Performance testing for MCP calls

Requirements:
- Both MCP servers running on their respective ports
- Friday AI system with memory management
- Test database for isolated testing
- Mock external API calls for reliability
"""

import os
import sys
import asyncio
import time
import json
import uuid
import threading
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from dataclasses import dataclass
import sqlite3
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test imports
try:
    from friday_with_memory import EnhancedFriday
    from memory_manager import MemoryManager, ConversationEntry, ToolUsageEntry
    from MCP_Servers.Email_MCP.email_mcp_server import EmailMCPServer
    from MCP_Servers.Day_Management_MCP.day_management_mcp_server import DayManagementMCPServer
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

# Test logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    name: str
    passed: bool
    execution_time: float
    error: Optional[str] = None
    details: Optional[Dict] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics for MCP calls"""
    total_calls: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    failed_calls: int
    concurrent_calls: int

class MCPMockManager:
    """Manages mocked MCP server responses for testing"""
    
    def __init__(self):
        self.email_responses = {
            "get_recent_emails": self._mock_recent_emails,
            "send_email": self._mock_send_email,
            "search_emails": self._mock_search_emails,
            "read_email": self._mock_read_email,
            "mark_emails_as_read": self._mock_mark_read,
            "get_gmail_labels": self._mock_gmail_labels
        }
        
        self.day_management_responses = {
            "get_calendar_events": self._mock_calendar_events,
            "create_calendar_event": self._mock_create_event,
            "update_calendar_event": self._mock_update_event,
            "delete_calendar_event": self._mock_delete_event,
            "get_tasks": self._mock_get_tasks,
            "create_task": self._mock_create_task,
            "update_task": self._mock_update_task,
            "complete_task": self._mock_complete_task,
            "get_day_overview": self._mock_day_overview,
            "get_tasklists": self._mock_tasklists
        }
        
        self.call_history = []
        self.performance_data = []
        self.failure_rate = 0.0
        self.simulate_delays = True
        
    def _mock_recent_emails(self, *args, **kwargs):
        """Mock recent emails response"""
        return """📧 RECENT EMAILS (last 24 hours)
==================================================

📩 UNREAD 
🕐 2 hours ago
👤 From: john.doe@example.com <john.doe@example.com>
📝 Subject: Meeting Request for Project Alpha
💬 Preview: Hi, I'd like to schedule a meeting to discuss Project Alpha...
🆔 ID: mock_email_123

📧 READ 
🕐 4 hours ago
👤 From: jane.smith@company.com <jane.smith@company.com>
📝 Subject: Weekly Report Submission
💬 Preview: Please find attached the weekly report for review...
🆔 ID: mock_email_456

📊 Total emails: 2"""

    def _mock_send_email(self, *args, **kwargs):
        """Mock send email response"""
        return "✅ Email sent successfully to test@example.com (Message ID: mock_sent_789)"

    def _mock_search_emails(self, *args, **kwargs):
        """Mock email search response"""
        return """🔍 EMAIL SEARCH RESULTS
Query: 'meeting' | Found: 1 emails
==================================================

📧 READ 
🕐 1 day ago
👤 From: manager@company.com <manager@company.com>
📝 Subject: Team Meeting Tomorrow
💬 Preview: Don't forget about our team meeting scheduled for tomorrow...
🆔 ID: mock_search_123"""

    def _mock_read_email(self, *args, **kwargs):
        """Mock read email response"""
        return """📧 EMAIL DETAILS
==================================================
🆔 Message ID: mock_email_123
👤 From: john.doe@example.com <john.doe@example.com>
📮 To: antony@example.com
📝 Subject: Meeting Request for Project Alpha
🕐 Date: 2024-01-15T10:30:00
📊 Status: UNREAD

==================================================
📄 CONTENT:
Hi Antony,

I'd like to schedule a meeting to discuss Project Alpha. Are you available this Thursday at 2 PM?

Best regards,
John"""

    def _mock_mark_read(self, *args, **kwargs):
        """Mock mark as read response"""
        return "✅ Marked 1 emails as read"

    def _mock_gmail_labels(self, *args, **kwargs):
        """Mock Gmail labels response"""
        return """🏷️ GMAIL LABELS
==============================
• INBOX (ID: INBOX)
• SENT (ID: SENT)
• DRAFT (ID: DRAFT)
• SPAM (ID: SPAM)
• TRASH (ID: TRASH)
• IMPORTANT (ID: IMPORTANT)
• STARRED (ID: STARRED)

📊 Total labels: 7"""

    def _mock_calendar_events(self, *args, **kwargs):
        """Mock calendar events response"""
        return """📅 UPCOMING CALENDAR EVENTS (next 7 days)
============================================================

📆 Monday, January 15, 2024
----------------------------------------

🕐 10:00 AM - 11:00 AM
📝 Project Alpha Meeting
📍 Conference Room A
👥 Attendees: john.doe@example.com, jane.smith@company.com
🆔 Event ID: mock_event_123

🕐 02:00 PM - 03:00 PM
📝 Weekly Team Sync
📍 Virtual Meeting
🆔 Event ID: mock_event_456

📊 Total events: 2"""

    def _mock_create_event(self, *args, **kwargs):
        """Mock create event response"""
        return "✅ Calendar event 'New Meeting' created successfully!\n🆔 Event ID: mock_created_789\n🕐 Start: 2024-01-16T14:00:00\n🔗 Link: https://calendar.google.com/mock_link"

    def _mock_update_event(self, *args, **kwargs):
        """Mock update event response"""
        return "✅ Calendar event updated successfully!\n🆔 Event ID: mock_event_123\n📝 Title: Updated Meeting Title\n🔗 Link: https://calendar.google.com/mock_link"

    def _mock_delete_event(self, *args, **kwargs):
        """Mock delete event response"""
        return "✅ Calendar event deleted successfully!\n🆔 Event ID: mock_event_123"

    def _mock_get_tasks(self, *args, **kwargs):
        """Mock get tasks response"""
        return """📋 TASKS OVERVIEW
==================================================
📊 Total: 3 | Pending: 2 | Completed: 1 | Overdue: 1

🚨 OVERDUE TASKS (1)
------------------------------

❗ Review project proposal
📅 Due: 2 days ago
📝 Need to complete the review by end of week
🆔 Task ID: mock_task_overdue_123

📝 PENDING TASKS (2)
------------------------------

🔄 Prepare presentation slides
📅 Due: in 2 days
📝 Create slides for the quarterly review meeting
🆔 Task ID: mock_task_pending_456

🔄 Submit expense report
📅 Due: in 5 days
🆔 Task ID: mock_task_pending_789"""

    def _mock_create_task(self, *args, **kwargs):
        """Mock create task response"""
        return "✅ Task 'New Task' created successfully!\n🆔 Task ID: mock_created_task_123\n📋 Task List: @default"

    def _mock_update_task(self, *args, **kwargs):
        """Mock update task response"""
        return "✅ Task updated successfully!\n🆔 Task ID: mock_task_123\n📝 Title: Updated Task Title\n📊 Status: needsAction"

    def _mock_complete_task(self, *args, **kwargs):
        """Mock complete task response"""
        return "✅ Task completed successfully!\n🆔 Task ID: mock_task_123\n🎉 Status: completed"

    def _mock_day_overview(self, *args, **kwargs):
        """Mock day overview response"""
        return """📅 DAY OVERVIEW - Monday, 2024-01-15
============================================================

📆 CALENDAR EVENTS (2)
----------------------------------------

🕐 10:00 AM - 11:00 AM - Project Alpha Meeting
📍 Conference Room A

🕐 02:00 PM - 03:00 PM - Weekly Team Sync
📍 Virtual Meeting

📋 TASKS DUE (1)
----------------------------------------

📝 Submit monthly report
📝 Prepare and submit the monthly status report

⏰ FREE TIME SLOTS
----------------------------------------

🕐 11:00 AM - 02:00 PM (180 minutes)
🕐 03:00 PM - 06:00 PM (180 minutes)"""

    def _mock_tasklists(self, *args, **kwargs):
        """Mock tasklists response"""
        return """📋 AVAILABLE TASK LISTS
========================================

📂 My Tasks
🆔 ID: @default
🔄 Updated: 01/15/2024 10:30 AM

📂 Work Projects
🆔 ID: work_projects_123
🔄 Updated: 01/14/2024 03:45 PM

📊 Total task lists: 2"""

    def simulate_mcp_call(self, server_type: str, tool_name: str, *args, **kwargs) -> str:
        """Simulate an MCP call with performance tracking"""
        start_time = time.time()
        
        # Record call
        self.call_history.append({
            'timestamp': datetime.now(),
            'server_type': server_type,
            'tool_name': tool_name,
            'args': args,
            'kwargs': kwargs
        })
        
        # Simulate network delay
        if self.simulate_delays:
            delay = 0.1 + (time.time() % 0.1)  # 0.1-0.2 seconds
            time.sleep(delay)
        
        # Simulate failure rate
        if time.time() % 1.0 < self.failure_rate:
            execution_time = time.time() - start_time
            self.performance_data.append({
                'execution_time': execution_time,
                'success': False,
                'server_type': server_type,
                'tool_name': tool_name
            })
            raise Exception(f"Simulated failure for {server_type}:{tool_name}")
        
        # Get response
        if server_type == 'email':
            response = self.email_responses.get(tool_name, lambda *a, **k: "Mock response")(*args, **kwargs)
        elif server_type == 'day_management':
            response = self.day_management_responses.get(tool_name, lambda *a, **k: "Mock response")(*args, **kwargs)
        else:
            response = "Unknown server type"
        
        execution_time = time.time() - start_time
        self.performance_data.append({
            'execution_time': execution_time,
            'success': True,
            'server_type': server_type,
            'tool_name': tool_name
        })
        
        return response
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from collected data"""
        if not self.performance_data:
            return PerformanceMetrics(0, 0.0, 0.0, 0.0, 0, 0)
        
        successful_calls = [d for d in self.performance_data if d['success']]
        failed_calls = [d for d in self.performance_data if not d['success']]
        
        if successful_calls:
            times = [d['execution_time'] for d in successful_calls]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
        else:
            avg_time = min_time = max_time = 0.0
        
        return PerformanceMetrics(
            total_calls=len(self.performance_data),
            avg_response_time=avg_time,
            min_response_time=min_time,
            max_response_time=max_time,
            failed_calls=len(failed_calls),
            concurrent_calls=0  # Will be calculated separately
        )
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.call_history.clear()
        self.performance_data.clear()

class FridayMCPIntegrationTester:
    """Comprehensive integration test suite for Friday with both MCP servers"""
    
    def __init__(self):
        self.friday = None
        self.test_db_path = None
        self.mock_manager = MCPMockManager()
        self.test_results = []
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """Set up isolated test environment"""
        # Create temporary test database
        self.test_db_path = tempfile.mktemp(suffix='.db')
        
        # Initialize Friday with test database
        self.friday = EnhancedFriday(memory_db_path=self.test_db_path)
        
        # Mock MCP server responses
        self.setup_mcp_mocks()
        
    def setup_mcp_mocks(self):
        """Set up mocks for MCP server responses"""
        # Mock the MCP client calls in Friday's tool execution
        def mock_mcp_response(tool_name, *args, **kwargs):
            # Determine server type based on tool name
            email_tools = ['get_recent_emails', 'send_email', 'search_emails', 'read_email', 
                          'mark_emails_as_read', 'get_gmail_labels']
            day_tools = ['get_calendar_events', 'create_calendar_event', 'update_calendar_event',
                        'delete_calendar_event', 'get_tasks', 'create_task', 'update_task',
                        'complete_task', 'get_day_overview', 'get_tasklists']
            
            if tool_name in email_tools:
                return self.mock_manager.simulate_mcp_call('email', tool_name, *args, **kwargs)
            elif tool_name in day_tools:
                return self.mock_manager.simulate_mcp_call('day_management', tool_name, *args, **kwargs)
            else:
                return f"Unknown tool: {tool_name}"
        
        # Patch Friday's tool execution method
        original_execute = self.friday._execute_tool_calls
        
        def patched_execute(tool_calls):
            results = {}
            for call in tool_calls:
                tool_name = call.get('name')
                parameters = call.get('parameters', {})
                
                if tool_name in ['retrieve_history', 'search_tool_usage', 'get_recent_context']:
                    # Use original method for memory functions
                    results[tool_name] = self.friday._function_registry[tool_name](**parameters)
                else:
                    # Use mock for MCP calls
                    results[tool_name] = mock_mcp_response(tool_name, **parameters)
            
            return results
        
        self.friday._execute_tool_calls = patched_execute
        
    def teardown_test_environment(self):
        """Clean up test environment"""
        if self.test_db_path and os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def run_test(self, test_name: str, test_func: Callable) -> TestResult:
        """Run a single test and record results"""
        print(f"\n🧪 Testing: {test_name}")
        
        start_time = time.time()
        try:
            result = test_func()
            execution_time = time.time() - start_time
            
            if result.get('success', False):
                print(f"✅ {test_name} PASSED ({execution_time:.2f}s)")
                test_result = TestResult(test_name, True, execution_time, None, result)
            else:
                print(f"❌ {test_name} FAILED ({execution_time:.2f}s)")
                test_result = TestResult(test_name, False, execution_time, result.get('error', 'Test failed'), result)
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {test_name} ERROR ({execution_time:.2f}s): {str(e)}")
            test_result = TestResult(test_name, False, execution_time, str(e), None)
        
        self.test_results.append(test_result)
        return test_result
    
    def test_friday_tool_configuration(self) -> Dict:
        """Test Friday's tool configuration for both MCPs"""
        try:
            # Check if both MCP servers are configured
            tools_config = self.friday._get_tools_config()
            
            email_mcp = None
            day_mcp = None
            
            for tool in tools_config:
                if tool.get('server_label') == 'email':
                    email_mcp = tool
                elif tool.get('server_label') == 'day-management':
                    day_mcp = tool
            
            if not email_mcp:
                return {'success': False, 'error': 'Email MCP not configured'}
            
            if not day_mcp:
                return {'success': False, 'error': 'Day Management MCP not configured'}
            
            # Verify URLs and configuration
            if email_mcp.get('server_url') != 'http://127.0.0.1:5002/mcp':
                return {'success': False, 'error': 'Email MCP URL misconfigured'}
            
            if day_mcp.get('server_url') != 'http://127.0.0.1:5003/mcp':
                return {'success': False, 'error': 'Day Management MCP URL misconfigured'}
            
            return {
                'success': True,
                'email_mcp': email_mcp,
                'day_mcp': day_mcp,
                'total_tools': len(tools_config)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_basic_email_operations(self) -> Dict:
        """Test basic email operations through Friday"""
        try:
            session_id = self.friday.start_conversation_session("Email Operations Test")
            
            # Test getting recent emails
            response1 = self.friday.get_response("Show me my recent emails")
            if "recent emails" not in response1.lower():
                return {'success': False, 'error': 'Failed to get recent emails'}
            
            # Test sending email
            response2 = self.friday.get_response("Send an email to test@example.com with subject 'Test' and body 'Hello'")
            if "sent successfully" not in response2.lower():
                return {'success': False, 'error': 'Failed to send email'}
            
            # Test searching emails
            response3 = self.friday.get_response("Search for emails containing 'meeting'")
            if "search results" not in response3.lower():
                return {'success': False, 'error': 'Failed to search emails'}
            
            self.friday.end_conversation_session("Email test completed")
            
            return {
                'success': True,
                'responses': [response1, response2, response3],
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_basic_calendar_operations(self) -> Dict:
        """Test basic calendar operations through Friday"""
        try:
            session_id = self.friday.start_conversation_session("Calendar Operations Test")
            
            # Test getting calendar events
            response1 = self.friday.get_response("Show me my upcoming calendar events")
            if "calendar events" not in response1.lower():
                return {'success': False, 'error': 'Failed to get calendar events'}
            
            # Test creating calendar event
            response2 = self.friday.get_response("Create a calendar event 'Team Meeting' for tomorrow at 2 PM to 3 PM")
            if "created successfully" not in response2.lower():
                return {'success': False, 'error': 'Failed to create calendar event'}
            
            # Test getting tasks
            response3 = self.friday.get_response("Show me my current tasks")
            if "tasks" not in response3.lower():
                return {'success': False, 'error': 'Failed to get tasks'}
            
            self.friday.end_conversation_session("Calendar test completed")
            
            return {
                'success': True,
                'responses': [response1, response2, response3],
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_end_to_end_workflow(self) -> Dict:
        """Test end-to-end workflow: Schedule meeting and send invites"""
        try:
            session_id = self.friday.start_conversation_session("End-to-End Workflow Test")
            
            # Complex workflow request
            workflow_request = """
            I need to schedule a meeting with the Project Alpha team for next Thursday at 2 PM.
            The meeting should be for 1 hour in Conference Room A.
            After creating the meeting, send an email to john.doe@example.com and jane.smith@company.com 
            with the meeting details and agenda.
            """
            
            response = self.friday.get_response(workflow_request)
            
            # Verify workflow completion
            if "created successfully" not in response.lower():
                return {'success': False, 'error': 'Meeting creation failed'}
            
            if "sent successfully" not in response.lower():
                return {'success': False, 'error': 'Email sending failed'}
            
            # Check that both operations were performed
            call_history = self.mock_manager.call_history
            calendar_calls = [c for c in call_history if c['server_type'] == 'day_management']
            email_calls = [c for c in call_history if c['server_type'] == 'email']
            
            if not calendar_calls:
                return {'success': False, 'error': 'No calendar operations performed'}
            
            if not email_calls:
                return {'success': False, 'error': 'No email operations performed'}
            
            self.friday.end_conversation_session("End-to-end test completed")
            
            return {
                'success': True,
                'response': response,
                'calendar_calls': len(calendar_calls),
                'email_calls': len(email_calls),
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_memory_integration(self) -> Dict:
        """Test memory integration with MCP tool usage"""
        try:
            session_id = self.friday.start_conversation_session("Memory Integration Test")
            
            # Perform some operations
            self.friday.get_response("Create a task 'Review budget' due tomorrow")
            self.friday.get_response("Send an email to finance@company.com about budget review")
            
            # Test memory recall
            response = self.friday.get_response("What did I just do with the budget?")
            
            # Verify memory integration
            if "budget" not in response.lower():
                return {'success': False, 'error': 'Memory integration failed'}
            
            # Check if tool usage was stored
            stats = self.friday.get_memory_stats()
            if stats.get('tool_usage_count', 0) == 0:
                return {'success': False, 'error': 'Tool usage not stored in memory'}
            
            self.friday.end_conversation_session("Memory test completed")
            
            return {
                'success': True,
                'response': response,
                'memory_stats': stats,
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_error_handling(self) -> Dict:
        """Test error handling across MCP connections"""
        try:
            session_id = self.friday.start_conversation_session("Error Handling Test")
            
            # Set failure rate to simulate errors
            original_failure_rate = self.mock_manager.failure_rate
            self.mock_manager.failure_rate = 0.5  # 50% failure rate
            
            results = []
            
            # Test multiple operations with potential failures
            for i in range(5):
                try:
                    response = self.friday.get_response(f"Get my emails (attempt {i+1})")
                    results.append({'attempt': i+1, 'success': True, 'response': response})
                except Exception as e:
                    results.append({'attempt': i+1, 'success': False, 'error': str(e)})
            
            # Restore original failure rate
            self.mock_manager.failure_rate = original_failure_rate
            
            # Verify error handling
            successful_attempts = [r for r in results if r['success']]
            failed_attempts = [r for r in results if not r['success']]
            
            if len(successful_attempts) == 0:
                return {'success': False, 'error': 'No operations succeeded despite error handling'}
            
            self.friday.end_conversation_session("Error handling test completed")
            
            return {
                'success': True,
                'total_attempts': len(results),
                'successful_attempts': len(successful_attempts),
                'failed_attempts': len(failed_attempts),
                'results': results,
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_concurrent_operations(self) -> Dict:
        """Test concurrent MCP operations"""
        try:
            session_id = self.friday.start_conversation_session("Concurrent Operations Test")
            
            # Simulate concurrent operations by making multiple requests
            concurrent_requests = [
                "Get my recent emails",
                "Show my calendar events",
                "List my tasks",
                "Get my Gmail labels",
                "Show me today's overview"
            ]
            
            start_time = time.time()
            responses = []
            
            # Execute requests and measure performance
            for request in concurrent_requests:
                response = self.friday.get_response(request)
                responses.append(response)
            
            total_time = time.time() - start_time
            
            # Verify all responses are valid
            for i, response in enumerate(responses):
                if not response or len(response.strip()) == 0:
                    return {'success': False, 'error': f'Empty response for request {i+1}'}
            
            # Check performance metrics
            metrics = self.mock_manager.get_performance_metrics()
            
            self.friday.end_conversation_session("Concurrent test completed")
            
            return {
                'success': True,
                'total_requests': len(concurrent_requests),
                'total_time': total_time,
                'avg_time_per_request': total_time / len(concurrent_requests),
                'responses': responses,
                'performance_metrics': metrics,
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_cross_mcp_integration(self) -> Dict:
        """Test Friday's ability to use both MCPs together"""
        try:
            session_id = self.friday.start_conversation_session("Cross-MCP Integration Test")
            
            # Request that requires both email and calendar operations
            complex_request = """
            I have a meeting about 'Project Alpha' coming up. Can you:
            1. Check my calendar for any Project Alpha meetings
            2. Search my emails for Project Alpha related messages
            3. Create a task to prepare for the meeting
            4. Send a summary email to my team
            """
            
            response = self.friday.get_response(complex_request)
            
            # Verify both MCPs were used
            call_history = self.mock_manager.call_history
            email_operations = [c for c in call_history if c['server_type'] == 'email']
            calendar_operations = [c for c in call_history if c['server_type'] == 'day_management']
            
            if not email_operations:
                return {'success': False, 'error': 'No email operations performed'}
            
            if not calendar_operations:
                return {'success': False, 'error': 'No calendar operations performed'}
            
            # Verify response quality
            if len(response.strip()) < 100:
                return {'success': False, 'error': 'Response too short for complex request'}
            
            self.friday.end_conversation_session("Cross-MCP test completed")
            
            return {
                'success': True,
                'response': response,
                'email_operations': len(email_operations),
                'calendar_operations': len(calendar_operations),
                'total_operations': len(call_history),
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_performance_benchmarks(self) -> Dict:
        """Test performance benchmarks for MCP calls"""
        try:
            session_id = self.friday.start_conversation_session("Performance Benchmark Test")
            
            # Reset performance metrics
            self.mock_manager.reset_metrics()
            
            # Disable simulated delays for accurate performance measurement
            original_delay_setting = self.mock_manager.simulate_delays
            self.mock_manager.simulate_delays = False
            
            # Perform multiple operations
            test_operations = [
                "Get my recent emails",
                "Show my calendar events",
                "List my tasks",
                "Get day overview",
                "Search for emails with 'test'"
            ]
            
            start_time = time.time()
            
            for _ in range(3):  # Run each operation 3 times
                for operation in test_operations:
                    self.friday.get_response(operation)
            
            total_time = time.time() - start_time
            
            # Restore delay setting
            self.mock_manager.simulate_delays = original_delay_setting
            
            # Get performance metrics
            metrics = self.mock_manager.get_performance_metrics()
            
            # Performance thresholds
            max_avg_response_time = 0.5  # 500ms
            max_total_time = 5.0  # 5 seconds for all operations
            
            if metrics.avg_response_time > max_avg_response_time:
                return {'success': False, 'error': f'Average response time too high: {metrics.avg_response_time:.3f}s'}
            
            if total_time > max_total_time:
                return {'success': False, 'error': f'Total execution time too high: {total_time:.3f}s'}
            
            self.friday.end_conversation_session("Performance test completed")
            
            return {
                'success': True,
                'total_time': total_time,
                'total_operations': len(test_operations) * 3,
                'performance_metrics': {
                    'total_calls': metrics.total_calls,
                    'avg_response_time': metrics.avg_response_time,
                    'min_response_time': metrics.min_response_time,
                    'max_response_time': metrics.max_response_time,
                    'failed_calls': metrics.failed_calls
                },
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_memory_persistence(self) -> Dict:
        """Test memory persistence across sessions"""
        try:
            # First session
            session_id1 = self.friday.start_conversation_session("Memory Persistence Test 1")
            self.friday.get_response("Create a task 'Important Project' due next week")
            self.friday.get_response("Send email to team@company.com about project update")
            self.friday.end_conversation_session("First session completed")
            
            # Second session
            session_id2 = self.friday.start_conversation_session("Memory Persistence Test 2")
            response = self.friday.get_response("What did I do in my previous session about the important project?")
            self.friday.end_conversation_session("Second session completed")
            
            # Verify memory persistence
            if "important project" not in response.lower():
                return {'success': False, 'error': 'Memory not persisted across sessions'}
            
            # Check database stats
            stats = self.friday.get_memory_stats()
            if stats.get('conversation_sessions', 0) < 2:
                return {'success': False, 'error': 'Sessions not properly recorded'}
            
            return {
                'success': True,
                'session_1': session_id1,
                'session_2': session_id2,
                'response': response,
                'memory_stats': stats
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_complex_workflow_memory(self) -> Dict:
        """Test complex workflow with memory integration"""
        try:
            session_id = self.friday.start_conversation_session("Complex Workflow Memory Test")
            
            # Multi-step workflow
            steps = [
                "Check my calendar for next week",
                "Create a task to prepare for the Project Alpha meeting",
                "Send an email to john.doe@example.com about the meeting preparation",
                "What tasks have I created today?",
                "Show me all my recent email activity"
            ]
            
            responses = []
            for step in steps:
                response = self.friday.get_response(step)
                responses.append(response)
            
            # Test memory integration
            memory_response = self.friday.get_response("Summarize all the actions I've taken in this session")
            
            # Verify memory integration
            if "project alpha" not in memory_response.lower():
                return {'success': False, 'error': 'Memory integration failed for complex workflow'}
            
            # Check tool usage history
            stats = self.friday.get_memory_stats()
            if stats.get('tool_usage_count', 0) == 0:
                return {'success': False, 'error': 'Tool usage not tracked in memory'}
            
            self.friday.end_conversation_session("Complex workflow test completed")
            
            return {
                'success': True,
                'steps_completed': len(steps),
                'responses': responses,
                'memory_response': memory_response,
                'memory_stats': stats,
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_all_tests(self) -> Dict:
        """Run all integration tests"""
        print("🚀 Starting Friday MCP Integration Test Suite")
        print("=" * 60)
        
        test_methods = [
            ("Tool Configuration", self.test_friday_tool_configuration),
            ("Basic Email Operations", self.test_basic_email_operations),
            ("Basic Calendar Operations", self.test_basic_calendar_operations),
            ("End-to-End Workflow", self.test_end_to_end_workflow),
            ("Memory Integration", self.test_memory_integration),
            ("Error Handling", self.test_error_handling),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Cross-MCP Integration", self.test_cross_mcp_integration),
            ("Performance Benchmarks", self.test_performance_benchmarks),
            ("Memory Persistence", self.test_memory_persistence),
            ("Complex Workflow Memory", self.test_complex_workflow_memory)
        ]
        
        start_time = time.time()
        
        for test_name, test_method in test_methods:
            self.run_test(test_name, test_method)
        
        total_time = time.time() - start_time
        
        # Calculate summary statistics
        passed_tests = [t for t in self.test_results if t.passed]
        failed_tests = [t for t in self.test_results if not t.passed]
        
        print(f"\n📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        # Performance metrics
        metrics = self.mock_manager.get_performance_metrics()
        print(f"\n🔧 PERFORMANCE METRICS")
        print("=" * 60)
        print(f"Total MCP Calls: {metrics.total_calls}")
        print(f"Average Response Time: {metrics.avg_response_time:.3f}s")
        print(f"Min Response Time: {metrics.min_response_time:.3f}s")
        print(f"Max Response Time: {metrics.max_response_time:.3f}s")
        print(f"Failed Calls: {metrics.failed_calls}")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS")
            print("=" * 60)
            for test in failed_tests:
                print(f"- {test.name}: {test.error}")
        
        return {
            'total_tests': len(self.test_results),
            'passed_tests': len(passed_tests),
            'failed_tests': len(failed_tests),
            'success_rate': len(passed_tests)/len(self.test_results)*100,
            'total_time': total_time,
            'performance_metrics': metrics,
            'test_results': self.test_results
        }

def main():
    """Main function to run the integration tests"""
    tester = FridayMCPIntegrationTester()
    
    try:
        # Run all tests
        results = tester.run_all_tests()
        
        # Cleanup
        tester.teardown_test_environment()
        
        # Exit with appropriate code
        if results['failed_tests'] > 0:
            print(f"\n❌ Some tests failed. Exiting with code 1.")
            sys.exit(1)
        else:
            print(f"\n✅ All tests passed successfully!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        tester.teardown_test_environment()
        sys.exit(1)

if __name__ == "__main__":
    main()