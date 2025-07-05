#!/usr/bin/env python3
"""
Example Usage of Friday MCP Integration Test Suite
This script demonstrates how the test suite works without requiring external dependencies
"""

import os
import sys
import time
from typing import Dict, Any

# Simulate the basic structure for demonstration
class MockFriday:
    """Mock Friday class for demonstration"""
    
    def __init__(self):
        self.conversations = []
        self.tool_calls = []
    
    def start_conversation_session(self, title):
        session_id = f"session_{len(self.conversations)}"
        self.conversations.append({"id": session_id, "title": title})
        return session_id
    
    def get_response(self, message):
        # Simulate tool usage based on message content
        if "email" in message.lower():
            self.tool_calls.append({"type": "email", "message": message})
            return "✅ Email operation completed successfully"
        elif "calendar" in message.lower() or "meeting" in message.lower():
            self.tool_calls.append({"type": "calendar", "message": message})
            return "✅ Calendar operation completed successfully"
        elif "task" in message.lower():
            self.tool_calls.append({"type": "tasks", "message": message})
            return "✅ Task operation completed successfully"
        else:
            return "I can help you with email, calendar, and task operations"
    
    def end_conversation_session(self, summary):
        if self.conversations:
            self.conversations[-1]["summary"] = summary

class ExampleTestRunner:
    """Example test runner demonstration"""
    
    def __init__(self):
        self.friday = MockFriday()
        self.test_results = []
    
    def run_example_test(self, test_name: str, test_func) -> Dict[str, Any]:
        """Run an example test"""
        print(f"\n🧪 Example Test: {test_name}")
        
        start_time = time.time()
        try:
            result = test_func()
            execution_time = time.time() - start_time
            
            if result.get('success', False):
                print(f"✅ {test_name} PASSED ({execution_time:.3f}s)")
                status = True
            else:
                print(f"❌ {test_name} FAILED ({execution_time:.3f}s)")
                status = False
            
            return {
                'name': test_name,
                'passed': status,
                'execution_time': execution_time,
                'details': result
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"💥 {test_name} ERROR ({execution_time:.3f}s): {str(e)}")
            return {
                'name': test_name,
                'passed': False,
                'execution_time': execution_time,
                'error': str(e)
            }
    
    def test_basic_email_operations(self) -> Dict:
        """Example email operations test"""
        session_id = self.friday.start_conversation_session("Email Test")
        
        # Test email operations
        response1 = self.friday.get_response("Show me my recent emails")
        response2 = self.friday.get_response("Send an email to test@example.com")
        
        self.friday.end_conversation_session("Email test completed")
        
        # Verify results
        email_calls = [call for call in self.friday.tool_calls if call['type'] == 'email']
        
        return {
            'success': len(email_calls) >= 2,
            'session_id': session_id,
            'responses': [response1, response2],
            'email_calls': len(email_calls)
        }
    
    def test_calendar_operations(self) -> Dict:
        """Example calendar operations test"""
        session_id = self.friday.start_conversation_session("Calendar Test")
        
        # Test calendar operations
        response1 = self.friday.get_response("Show my calendar events")
        response2 = self.friday.get_response("Create a meeting for tomorrow")
        
        self.friday.end_conversation_session("Calendar test completed")
        
        # Verify results
        calendar_calls = [call for call in self.friday.tool_calls if call['type'] == 'calendar']
        
        return {
            'success': len(calendar_calls) >= 2,
            'session_id': session_id,
            'responses': [response1, response2],
            'calendar_calls': len(calendar_calls)
        }
    
    def test_end_to_end_workflow(self) -> Dict:
        """Example end-to-end workflow test"""
        session_id = self.friday.start_conversation_session("E2E Workflow Test")
        
        # Complex workflow
        workflow_request = """
        Schedule a team meeting for next Friday at 2 PM and send invites to the team.
        Also create a task to prepare the agenda.
        """
        
        response = self.friday.get_response(workflow_request)
        
        self.friday.end_conversation_session("E2E test completed")
        
        # Check if multiple tool types were used
        email_calls = [call for call in self.friday.tool_calls if call['type'] == 'email']
        calendar_calls = [call for call in self.friday.tool_calls if call['type'] == 'calendar']
        task_calls = [call for call in self.friday.tool_calls if call['type'] == 'tasks']
        
        return {
            'success': len(email_calls) > 0 and len(calendar_calls) > 0,
            'session_id': session_id,
            'response': response,
            'email_calls': len(email_calls),
            'calendar_calls': len(calendar_calls),
            'task_calls': len(task_calls)
        }
    
    def run_example_tests(self):
        """Run all example tests"""
        print("🚀 Friday MCP Integration Test Suite - Example Usage")
        print("=" * 60)
        print("This demonstrates how the real test suite would work")
        print("(This example uses mocks and doesn't require external dependencies)")
        
        tests = [
            ("Basic Email Operations", self.test_basic_email_operations),
            ("Calendar Operations", self.test_calendar_operations),
            ("End-to-End Workflow", self.test_end_to_end_workflow)
        ]
        
        start_time = time.time()
        
        for test_name, test_func in tests:
            result = self.run_example_test(test_name, test_func)
            self.test_results.append(result)
        
        total_time = time.time() - start_time
        
        # Generate summary
        passed_tests = [t for t in self.test_results if t['passed']]
        failed_tests = [t for t in self.test_results if not t['passed']]
        
        print(f"\n📊 EXAMPLE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        print(f"Total Time: {total_time:.3f}s")
        
        print(f"\n🔧 MOCK INTEGRATION STATS")
        print("=" * 60)
        print(f"Total Tool Calls: {len(self.friday.tool_calls)}")
        print(f"Email Operations: {len([c for c in self.friday.tool_calls if c['type'] == 'email'])}")
        print(f"Calendar Operations: {len([c for c in self.friday.tool_calls if c['type'] == 'calendar'])}")
        print(f"Task Operations: {len([c for c in self.friday.tool_calls if c['type'] == 'tasks'])}")
        print(f"Conversation Sessions: {len(self.friday.conversations)}")
        
        if self.test_results:
            print(f"\n📋 DETAILED RESULTS")
            print("=" * 60)
            for result in self.test_results:
                status = "✅" if result['passed'] else "❌"
                print(f"{status} {result['name']}: {result['execution_time']:.3f}s")
                if 'details' in result and result['details']:
                    details = result['details']
                    if 'email_calls' in details:
                        print(f"   📧 Email calls: {details['email_calls']}")
                    if 'calendar_calls' in details:
                        print(f"   📅 Calendar calls: {details['calendar_calls']}")
                    if 'task_calls' in details:
                        print(f"   📋 Task calls: {details['task_calls']}")
        
        print(f"\n🎯 COMPARISON WITH REAL TEST SUITE")
        print("=" * 60)
        print("The real test suite includes:")
        print("• 11 comprehensive test methods")
        print("• Sophisticated MCP server mocking")
        print("• Memory integration testing")
        print("• Performance benchmarking")
        print("• Error handling and recovery testing")
        print("• Concurrent operation testing")
        print("• Cross-session memory persistence")
        print("• Detailed HTML/JSON/Markdown reporting")
        print("• Configurable failure simulation")
        print("• Performance metrics and thresholds")
        
        return len(passed_tests) == len(self.test_results)

def main():
    """Main function for example usage"""
    runner = ExampleTestRunner()
    success = runner.run_example_tests()
    
    print(f"\n💡 NEXT STEPS")
    print("=" * 60)
    print("To run the real integration test suite:")
    print("1. Ensure all Friday dependencies are installed")
    print("2. Run: python3 run_integration_tests.py")
    print("3. Or run specific tests: python3 run_integration_tests.py --tests email_operations")
    print("4. Check generated reports in test_reports/ directory")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())