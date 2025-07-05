#!/usr/bin/env python3
"""
Simple Test Runner for Day Management MCP Server

This is a basic test runner that can validate the test suite structure
and run basic import tests without requiring external testing frameworks.
"""

import os
import sys
import importlib
import traceback
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    test_modules = [
        'json',
        'asyncio', 
        'datetime',
        'typing',
        'unittest.mock',
        'pytz',
        'dateutil.parser'
    ]
    
    failed_imports = []
    
    for module in test_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    # Test Day Management MCP Server import
    try:
        from MCP_Servers.Day_Management_MCP.day_management_mcp_server import DayManagementMCPServer
        print("✅ Day Management MCP Server")
    except ImportError as e:
        print(f"❌ Day Management MCP Server: {e}")
        failed_imports.append("Day Management MCP Server")
    
    return len(failed_imports) == 0

def test_server_creation():
    """Test basic server creation"""
    print("\n🔧 Testing server creation...")
    
    try:
        from MCP_Servers.Day_Management_MCP.day_management_mcp_server import DayManagementMCPServer
        
        # This should work without actual Google credentials
        server = DayManagementMCPServer()
        
        # Check basic attributes
        assert hasattr(server, 'credentials_path')
        assert hasattr(server, 'token_path')
        assert hasattr(server, 'timezone')
        
        print("✅ Server creation successful")
        print(f"   Credentials path: {server.credentials_path}")
        print(f"   Token path: {server.token_path}")
        print(f"   Timezone: {server.timezone}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        traceback.print_exc()
        return False

def test_data_classes():
    """Test data class definitions"""
    print("\n📊 Testing data classes...")
    
    try:
        from MCP_Servers.Day_Management_MCP.day_management_mcp_server import CalendarEvent, Task
        from datetime import datetime
        
        # Test CalendarEvent
        event = CalendarEvent(
            event_id='test',
            calendar_id='primary',
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_time=datetime.now(),
            end_time=datetime.now(),
            timezone='UTC',
            attendees=[],
            is_all_day=False,
            recurrence=None,
            status='confirmed',
            creator_email='test@example.com',
            organizer_email='test@example.com'
        )
        
        assert event.title == 'Test Event'
        print("✅ CalendarEvent class")
        
        # Test Task
        task = Task(
            task_id='test',
            tasklist_id='@default',
            title='Test Task',
            notes='Test Notes',
            status='needsAction',
            due_date=None,
            completed_date=None,
            parent_task_id=None,
            position='',
            links=[]
        )
        
        assert task.title == 'Test Task'
        print("✅ Task class")
        
        return True
        
    except Exception as e:
        print(f"❌ Data class test failed: {e}")
        traceback.print_exc()
        return False

def test_async_methods():
    """Test that async methods are properly defined"""
    print("\n⚡ Testing async method definitions...")
    
    try:
        from MCP_Servers.Day_Management_MCP.day_management_mcp_server import DayManagementMCPServer
        import inspect
        
        server = DayManagementMCPServer()
        
        async_methods = [
            'get_calendar_events',
            'create_calendar_event',
            'update_calendar_event',
            'delete_calendar_event',
            'get_tasks',
            'create_task',
            'update_task',
            'complete_task',
            'get_tasklists',
            'get_day_overview'
        ]
        
        for method_name in async_methods:
            method = getattr(server, method_name)
            assert inspect.iscoroutinefunction(method), f"{method_name} should be async"
            print(f"✅ {method_name} (async)")
        
        return True
        
    except Exception as e:
        print(f"❌ Async method test failed: {e}")
        traceback.print_exc()
        return False

def test_mcp_tools():
    """Test MCP tool definitions"""
    print("\n🛠️ Testing MCP tool definitions...")
    
    try:
        # Import the MCP tools
        from MCP_Servers.Day_Management_MCP import day_management_mcp_server
        
        # Check if tools are defined as functions
        mcp_tools = [
            'get_calendar_events',
            'create_calendar_event',
            'update_calendar_event',
            'delete_calendar_event',
            'get_tasks',
            'create_task',
            'update_task',
            'complete_task',
            'get_tasklists',
            'get_day_overview'
        ]
        
        for tool_name in mcp_tools:
            if hasattr(day_management_mcp_server, tool_name):
                tool_func = getattr(day_management_mcp_server, tool_name)
                if callable(tool_func):
                    print(f"✅ {tool_name} (MCP tool)")
                else:
                    print(f"⚠️  {tool_name} exists but not callable")
            else:
                print(f"❌ {tool_name} not found")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP tool test failed: {e}")
        traceback.print_exc()
        return False

def validate_test_file():
    """Validate the comprehensive test file structure"""
    print("\n📝 Validating comprehensive test file...")
    
    test_file = Path(__file__).parent / "test_day_management_comprehensive.py"
    
    if not test_file.exists():
        print("❌ Comprehensive test file not found")
        return False
    
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Check for required test classes
        required_classes = [
            'TestDayManagementMCPServer',
            'TestDayManagementServerInitialization',
            'TestOAuth2Authentication',
            'TestCalendarEventManagement',
            'TestTaskManagement',
            'TestDayOverview',
            'TestTimezoneHandling',
            'TestSmartScheduling',
            'TestMCPTools',
            'TestFridayIntegration',
            'TestErrorHandling',
            'TestDataConversion',
            'TestPerformanceAndScaling'
        ]
        
        found_classes = []
        missing_classes = []
        
        for test_class in required_classes:
            if f"class {test_class}" in content:
                found_classes.append(test_class)
                print(f"✅ {test_class}")
            else:
                missing_classes.append(test_class)
                print(f"❌ {test_class}")
        
        # Check for key imports
        required_imports = [
            'import pytest',
            'from unittest.mock import',
            '@pytest.fixture',
            '@pytest.mark.asyncio'
        ]
        
        for import_check in required_imports:
            if import_check in content:
                print(f"✅ {import_check}")
            else:
                print(f"❌ {import_check}")
        
        print(f"\n📊 Test classes: {len(found_classes)}/{len(required_classes)} found")
        print(f"📄 Test file size: {len(content)} characters")
        
        return len(missing_classes) == 0
        
    except Exception as e:
        print(f"❌ Test file validation failed: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("\n🔧 Checking environment...")
    
    env_vars = [
        'GOOGLE_CREDENTIALS_PATH',
        'GOOGLE_TOKEN_PATH', 
        'USER_TIMEZONE',
        'OPENAI_API_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set")
    
    # Check for credentials file
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'day_credentials.json')
    if os.path.exists(creds_path):
        print(f"✅ Credentials file found: {creds_path}")
    else:
        print(f"⚠️  Credentials file not found: {creds_path}")
    
    return True

def run_all_tests():
    """Run all basic tests"""
    print("🚀 Running Day Management MCP Server Basic Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Server Creation", test_server_creation),
        ("Data Classes", test_data_classes),
        ("Async Methods", test_async_methods),
        ("MCP Tools", test_mcp_tools),
        ("Test File Validation", validate_test_file),
        ("Environment Check", check_environment)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All basic tests passed!")
        print("\n📋 Next Steps:")
        print("1. Install pytest: pip install pytest pytest-asyncio pytest-mock")
        print("2. Run comprehensive tests: python run_tests.py --all")
        print("3. Set up Google OAuth2 credentials for live testing")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("Review the output above and fix any issues.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)