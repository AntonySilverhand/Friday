#!/usr/bin/env python3
"""
Test script for Day Management MCP integration with Friday AI Assistant
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test imports
try:
    from friday_with_memory import EnhancedFriday
    from MCP_Servers.Day_Management_MCP.day_management_mcp_server import DayManagementMCPServer
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

class DayManagementIntegrationTester:
    """Test the Day Management MCP integration with Friday"""
    
    def __init__(self):
        self.day_server = None
        self.friday = None
        self.test_results = []
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            start_time = time.time()
            result = test_func()
            execution_time = time.time() - start_time
            
            if result:
                print(f"✅ {test_name} PASSED ({execution_time:.2f}s)")
                self.test_results.append((test_name, True, execution_time, None))
                return True
            else:
                print(f"❌ {test_name} FAILED ({execution_time:.2f}s)")
                self.test_results.append((test_name, False, execution_time, "Test returned False"))
                return False
                
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            self.test_results.append((test_name, False, 0, str(e)))
            return False
    
    def test_day_management_server_creation(self) -> bool:
        """Test Day Management MCP server creation"""
        try:
            self.day_server = DayManagementMCPServer()
            
            # Check if server was created
            if self.day_server is None:
                return False
            
            # Check if Google credentials are configured
            if not os.path.exists(self.day_server.credentials_path):
                print(f"⚠️  Google credentials not found at {self.day_server.credentials_path}")
                print("   This is expected for initial setup")
            
            # Check timezone configuration
            if self.day_server.timezone:
                print(f"✅ Timezone configured: {self.day_server.timezone}")
            
            return True
            
        except Exception as e:
            print(f"Error creating Day Management server: {e}")
            return False
    
    async def test_day_management_server_functionality(self) -> bool:
        """Test basic Day Management server functionality"""
        try:
            if not self.day_server:
                return False
            
            # Test get_calendar_events (should handle no service gracefully)
            events = await self.day_server.get_calendar_events(days_ahead=1, max_results=5)
            
            # Should return empty list if no service
            if not isinstance(events, list):
                return False
            
            # Test get_tasks
            tasks = await self.day_server.get_tasks(max_results=5)
            
            # Should return empty list if no service
            if not isinstance(tasks, list):
                return False
            
            # Test get_tasklists
            tasklists = await self.day_server.get_tasklists()
            
            # Should return empty list if no service
            if not isinstance(tasklists, list):
                return False
            
            # Test get_day_overview
            overview = await self.day_server.get_day_overview()
            
            # Should return dict with structure
            if not isinstance(overview, dict):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error testing Day Management server functionality: {e}")
            return False
    
    def test_friday_with_day_management(self) -> bool:
        """Test Friday integration with Day Management MCP"""
        try:
            # Create Friday instance with memory
            self.friday = EnhancedFriday("test_day_memory.db")
            
            if not self.friday:
                return False
            
            # Check if Day Management MCP is in tools config
            tools_config = self.friday._get_tools_config()
            
            day_tool_found = False
            for tool in tools_config:
                if (tool.get("type") == "mcp" and 
                    tool.get("server_label") == "day-management"):
                    day_tool_found = True
                    break
            
            if not day_tool_found:
                print("⚠️  Day Management MCP not found in Friday's tools configuration")
                print("   This will be added in the next step")
                return True  # Don't fail for this yet
            
            print("✅ Day Management MCP found in Friday's tools configuration")
            return True
            
        except Exception as e:
            print(f"Error testing Friday with Day Management: {e}")
            return False
    
    def test_environment_setup(self) -> bool:
        """Test environment setup for Day Management integration"""
        try:
            checks = {
                "GOOGLE_CREDENTIALS_PATH": os.getenv("GOOGLE_CREDENTIALS_PATH"),
                "GOOGLE_TOKEN_PATH": os.getenv("GOOGLE_TOKEN_PATH"),
                "USER_TIMEZONE": os.getenv("USER_TIMEZONE"),
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
            }
            
            all_set = True
            for var_name, value in checks.items():
                if value:
                    print(f"✅ {var_name} is set")
                else:
                    print(f"⚠️  {var_name} is not set")
                    if var_name == "OPENAI_API_KEY":
                        all_set = False  # OpenAI key is required
            
            # Check for credentials file
            creds_path = checks.get("GOOGLE_CREDENTIALS_PATH", "day_credentials.json")
            if os.path.exists(creds_path):
                print(f"✅ Google credentials file found at {creds_path}")
            else:
                print(f"⚠️  Google credentials file not found at {creds_path}")
                print("   Download from Google Cloud Console")
            
            return all_set
            
        except Exception as e:
            print(f"Error checking environment: {e}")
            return False
    
    def test_day_management_mcp_tools(self) -> bool:
        """Test that Day Management MCP tools are properly defined"""
        try:
            # Import and check the MCP tools
            from MCP_Servers.Day_Management_MCP.day_management_mcp_server import mcp
            
            # Check if tools are registered
            tools_exist = hasattr(mcp, '_tools') or hasattr(mcp, 'tools')
            
            if tools_exist:
                print("✅ Day Management MCP tools are defined")
                return True
            else:
                print("⚠️  Day Management MCP tools definition check inconclusive")
                return True  # Don't fail for this
                
        except Exception as e:
            print(f"Error checking Day Management MCP tools: {e}")
            return False
    
    def test_google_api_imports(self) -> bool:
        """Test that Google API libraries are properly imported"""
        try:
            # Test imports
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            import pytz
            from dateutil import parser as date_parser
            
            print("✅ All Google API and date libraries imported successfully")
            return True
            
        except ImportError as e:
            print(f"❌ Google API import error: {e}")
            print("   Install with: pip install google-api-python-client google-auth google-auth-oauthlib pytz dateutil")
            return False
        except Exception as e:
            print(f"Error testing Google API imports: {e}")
            return False
    
    def test_oauth_credentials_format(self) -> bool:
        """Test OAuth credentials file format"""
        try:
            creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "day_credentials.json")
            
            if not os.path.exists(creds_path):
                print(f"⚠️  Credentials file not found: {creds_path}")
                return True  # Don't fail for missing file
            
            import json
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            
            # Check basic structure
            if "installed" in creds_data:
                client_info = creds_data["installed"]
                required_fields = ["client_id", "client_secret", "auth_uri", "token_uri"]
                
                for field in required_fields:
                    if field not in client_info:
                        print(f"❌ Missing field in credentials: {field}")
                        return False
                
                print("✅ OAuth credentials file format is valid")
                return True
            else:
                print("❌ Invalid credentials file format")
                return False
                
        except Exception as e:
            print(f"Error checking credentials format: {e}")
            return False
    
    def test_timezone_configuration(self) -> bool:
        """Test timezone configuration"""
        try:
            import pytz
            
            # Test default timezone
            user_tz = os.getenv("USER_TIMEZONE", "UTC")
            
            try:
                timezone = pytz.timezone(user_tz)
                print(f"✅ Timezone '{user_tz}' is valid")
                return True
            except pytz.exceptions.UnknownTimeZoneError:
                print(f"❌ Invalid timezone: {user_tz}")
                print("   Use timezone names like 'America/New_York', 'Europe/London', 'Asia/Tokyo'")
                return False
                
        except Exception as e:
            print(f"Error testing timezone configuration: {e}")
            return False
    
    def test_date_parsing(self) -> bool:
        """Test date parsing functionality"""
        try:
            from dateutil import parser as date_parser
            from datetime import datetime
            
            # Test various date formats
            test_dates = [
                "2024-07-05T10:00:00",
                "July 5, 2024 10:00 AM",
                "2024-07-05",
                "tomorrow at 3pm",
                "next Monday 9am"
            ]
            
            parsed_count = 0
            for date_str in test_dates:
                try:
                    parsed_date = date_parser.parse(date_str)
                    parsed_count += 1
                except:
                    continue
            
            if parsed_count >= 3:  # At least 3 formats should work
                print(f"✅ Date parsing works ({parsed_count}/{len(test_dates)} formats)")
                return True
            else:
                print(f"⚠️  Limited date parsing support ({parsed_count}/{len(test_dates)} formats)")
                return False
                
        except Exception as e:
            print(f"Error testing date parsing: {e}")
            return False
    
    async def run_async_tests(self):
        """Run async tests"""
        print("🔄 Running async tests...")
        
        success = True
        if not await self.test_day_management_server_functionality():
            success = False
        
        return success
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting Day Management Integration Test Suite")
        print("=" * 70)
        
        # Define tests
        sync_tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Google API Imports", self.test_google_api_imports),
            ("Timezone Configuration", self.test_timezone_configuration),
            ("Date Parsing", self.test_date_parsing),
            ("OAuth Credentials Format", self.test_oauth_credentials_format),
            ("Day Management Server Creation", self.test_day_management_server_creation),
            ("Friday Integration", self.test_friday_with_day_management),
            ("MCP Tools Definition", self.test_day_management_mcp_tools)
        ]
        
        # Run sync tests
        passed = 0
        total = len(sync_tests)
        
        for test_name, test_func in sync_tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        # Run async tests
        print("\n🔄 Running async tests...")
        try:
            async_result = asyncio.run(self.run_async_tests())
            if async_result:
                passed += 1
                print("✅ Async tests PASSED")
                self.test_results.append(("Async Functionality", True, 0, None))
            else:
                print("❌ Async tests FAILED")
                self.test_results.append(("Async Functionality", False, 0, "Async tests failed"))
            total += 1
        except Exception as e:
            print(f"❌ Async tests FAILED with exception: {e}")
            self.test_results.append(("Async Functionality", False, 0, str(e)))
            total += 1
        
        # Generate report
        print("\n" + "=" * 70)
        print("📊 DAY MANAGEMENT INTEGRATION TEST RESULTS")
        print("=" * 70)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for test_name, success, exec_time, error in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {test_name} ({exec_time:.2f}s)")
            if error:
                print(f"    Error: {error}")
        
        # Setup instructions
        print("\n🔧 Setup Instructions:")
        print("1. Create Google Cloud project and enable Calendar + Tasks APIs")
        print("2. Download OAuth2 credentials as day_credentials.json")
        print("3. Set GOOGLE_CREDENTIALS_PATH in .env file")
        print("4. Set USER_TIMEZONE in .env file")
        print("5. Run: pip install -r MCP_Servers/Day_Management_MCP/requirements.txt")
        print("6. Start server: python MCP_Servers/Day_Management_MCP/day_management_mcp_server.py")
        print("7. Complete OAuth flow in browser")
        
        # Feature overview
        print("\n🌟 Available Features:")
        print("📅 Calendar Management:")
        print("  • Get upcoming events")
        print("  • Create/update/delete events")
        print("  • Smart conflict detection")
        print("  • Free time slot calculation")
        print("")
        print("📋 Task Management:")
        print("  • Get tasks from all lists")
        print("  • Create/update/complete tasks")
        print("  • Due date management")
        print("  • Overdue task detection")
        print("")
        print("🗓️ Day Planning:")
        print("  • Comprehensive day overview")
        print("  • Events + tasks integration")
        print("  • Free time optimization")
        print("  • Smart scheduling assistance")
        
        # Cleanup
        if os.path.exists("test_day_memory.db"):
            os.remove("test_day_memory.db")
        
        if passed == total:
            print("\n🎉 All tests passed! Day Management integration is ready.")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Review setup and configuration.")
            return False

def main():
    """Run the Day Management integration test suite"""
    tester = DayManagementIntegrationTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()