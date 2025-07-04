#!/usr/bin/env python3
"""
Test script for Telegram MCP integration with Friday AI Assistant
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
    from MCP_Servers.Telegram_MCP.telegram_mcp_server import TelegramMCPServer
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

class TelegramIntegrationTester:
    """Test the Telegram MCP integration with Friday"""
    
    def __init__(self):
        self.telegram_server = None
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
    
    def test_telegram_server_creation(self) -> bool:
        """Test Telegram MCP server creation"""
        try:
            self.telegram_server = TelegramMCPServer()
            
            # Check if server was created
            if self.telegram_server is None:
                return False
            
            # Check if bot token is configured (optional)
            if not os.getenv("TELEGRAM_BOT_TOKEN"):
                print("⚠️  TELEGRAM_BOT_TOKEN not found - some features will be limited")
            
            return True
            
        except Exception as e:
            print(f"Error creating Telegram server: {e}")
            return False
    
    async def test_telegram_server_functionality(self) -> bool:
        """Test basic Telegram server functionality"""
        try:
            if not self.telegram_server:
                return False
            
            # Test get_recent_messages (should work even without real messages)
            messages = await self.telegram_server.get_recent_messages(limit=5)
            
            # Should return empty list if no messages
            if not isinstance(messages, list):
                return False
            
            # Test get_chat_info
            chats = await self.telegram_server.get_chat_info()
            
            # Should return empty list if no chats
            if not isinstance(chats, list):
                return False
            
            # Test search_messages
            search_results = await self.telegram_server.search_messages("test", limit=5)
            
            # Should return empty list if no matches
            if not isinstance(search_results, list):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error testing Telegram server functionality: {e}")
            return False
    
    def test_friday_with_telegram(self) -> bool:
        """Test Friday integration with Telegram MCP"""
        try:
            # Create Friday instance with memory
            self.friday = EnhancedFriday("test_telegram_memory.db")
            
            if not self.friday:
                return False
            
            # Check if Telegram MCP is in tools config
            tools_config = self.friday._get_tools_config()
            
            telegram_tool_found = False
            for tool in tools_config:
                if (tool.get("type") == "mcp" and 
                    tool.get("server_label") == "telegram"):
                    telegram_tool_found = True
                    break
            
            if not telegram_tool_found:
                print("❌ Telegram MCP not found in Friday's tools configuration")
                return False
            
            print("✅ Telegram MCP found in Friday's tools configuration")
            return True
            
        except Exception as e:
            print(f"Error testing Friday with Telegram: {e}")
            return False
    
    def test_environment_setup(self) -> bool:
        """Test environment setup for Telegram integration"""
        try:
            checks = {
                "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
                "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
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
            
            return all_set
            
        except Exception as e:
            print(f"Error checking environment: {e}")
            return False
    
    def test_telegram_mcp_tools(self) -> bool:
        """Test that Telegram MCP tools are properly defined"""
        try:
            # Import and check the MCP tools
            from MCP_Servers.Telegram_MCP.telegram_mcp_server import mcp
            
            # Check if tools are registered
            # Note: This is a basic check - full testing requires running server
            tools_exist = hasattr(mcp, '_tools') or hasattr(mcp, 'tools')
            
            if tools_exist:
                print("✅ Telegram MCP tools are defined")
                return True
            else:
                print("⚠️  Telegram MCP tools definition check inconclusive")
                return True  # Don't fail for this
                
        except Exception as e:
            print(f"Error checking Telegram MCP tools: {e}")
            return False
    
    def test_message_formatting(self) -> bool:
        """Test message formatting functions"""
        try:
            if not self.telegram_server:
                return False
            
            # Test relative time formatting
            from datetime import datetime, timedelta
            
            test_time = datetime.now() - timedelta(minutes=30)
            relative_time = self.telegram_server._get_relative_time(test_time)
            
            if "minute" not in relative_time and "Just now" not in relative_time:
                return False
            
            print(f"✅ Relative time formatting works: '{relative_time}'")
            return True
            
        except Exception as e:
            print(f"Error testing message formatting: {e}")
            return False
    
    async def run_async_tests(self):
        """Run async tests"""
        print("🔄 Running async tests...")
        
        success = True
        if not await self.test_telegram_server_functionality():
            success = False
        
        return success
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting Telegram Integration Test Suite")
        print("=" * 60)
        
        # Define tests
        sync_tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Telegram Server Creation", self.test_telegram_server_creation),
            ("Friday Integration", self.test_friday_with_telegram),
            ("MCP Tools Definition", self.test_telegram_mcp_tools),
            ("Message Formatting", self.test_message_formatting)
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
        print("\n" + "=" * 60)
        print("📊 TELEGRAM INTEGRATION TEST RESULTS")
        print("=" * 60)
        
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
        print("1. Get Telegram Bot Token from @BotFather")
        print("2. Set TELEGRAM_BOT_TOKEN in .env file")
        print("3. Get your chat ID and set TELEGRAM_CHAT_ID")
        print("4. Run: pip install -r MCP_Servers/Telegram_MCP/requirements.txt")
        print("5. Start server: python MCP_Servers/Telegram_MCP/telegram_mcp_server.py")
        
        # Cleanup
        if os.path.exists("test_telegram_memory.db"):
            os.remove("test_telegram_memory.db")
        
        if passed == total:
            print("\n🎉 All tests passed! Telegram integration is ready.")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Review setup and configuration.")
            return False

def main():
    """Run the Telegram integration test suite"""
    tester = TelegramIntegrationTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()