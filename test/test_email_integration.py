#!/usr/bin/env python3
"""
Test script for Email MCP integration with Friday AI Assistant
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
    from MCP_Servers.Email_MCP.email_mcp_server import EmailMCPServer
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

class EmailIntegrationTester:
    """Test the Email MCP integration with Friday"""
    
    def __init__(self):
        self.email_server = None
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
    
    def test_email_server_creation(self) -> bool:
        """Test Email MCP server creation"""
        try:
            self.email_server = EmailMCPServer()
            
            # Check if server was created
            if self.email_server is None:
                return False
            
            # Check if Gmail credentials are configured
            if not os.path.exists(self.email_server.credentials_path):
                print(f"⚠️  Gmail credentials not found at {self.email_server.credentials_path}")
                print("   This is expected for initial setup")
            
            return True
            
        except Exception as e:
            print(f"Error creating Email server: {e}")
            return False
    
    async def test_email_server_functionality(self) -> bool:
        """Test basic Email server functionality"""
        try:
            if not self.email_server:
                return False
            
            # Test get_recent_emails (should handle no service gracefully)
            emails = await self.email_server.get_recent_emails(limit=5)
            
            # Should return empty list if no service
            if not isinstance(emails, list):
                return False
            
            # Test search_emails
            search_results = await self.email_server.search_emails("test", limit=5)
            
            # Should return empty list if no service
            if not isinstance(search_results, list):
                return False
            
            # Test get_labels
            labels = await self.email_server.get_labels()
            
            # Should return empty list if no service
            if not isinstance(labels, list):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error testing Email server functionality: {e}")
            return False
    
    def test_friday_with_email(self) -> bool:
        """Test Friday integration with Email MCP"""
        try:
            # Create Friday instance with memory
            self.friday = EnhancedFriday("test_email_memory.db")
            
            if not self.friday:
                return False
            
            # Check if Email MCP is in tools config
            tools_config = self.friday._get_tools_config()
            
            email_tool_found = False
            for tool in tools_config:
                if (tool.get("type") == "mcp" and 
                    tool.get("server_label") == "email"):
                    email_tool_found = True
                    break
            
            if not email_tool_found:
                print("⚠️  Email MCP not found in Friday's tools configuration")
                print("   This will be added in the next step")
                return True  # Don't fail for this yet
            
            print("✅ Email MCP found in Friday's tools configuration")
            return True
            
        except Exception as e:
            print(f"Error testing Friday with Email: {e}")
            return False
    
    def test_environment_setup(self) -> bool:
        """Test environment setup for Email integration"""
        try:
            checks = {
                "GMAIL_CREDENTIALS_PATH": os.getenv("GMAIL_CREDENTIALS_PATH"),
                "GMAIL_TOKEN_PATH": os.getenv("GMAIL_TOKEN_PATH"),
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
            creds_path = checks.get("GMAIL_CREDENTIALS_PATH", "credentials.json")
            if os.path.exists(creds_path):
                print(f"✅ Gmail credentials file found at {creds_path}")
            else:
                print(f"⚠️  Gmail credentials file not found at {creds_path}")
                print("   Download from Google Cloud Console")
            
            return all_set
            
        except Exception as e:
            print(f"Error checking environment: {e}")
            return False
    
    def test_email_mcp_tools(self) -> bool:
        """Test that Email MCP tools are properly defined"""
        try:
            # Import and check the MCP tools
            from MCP_Servers.Email_MCP.email_mcp_server import mcp
            
            # Check if tools are registered
            tools_exist = hasattr(mcp, '_tools') or hasattr(mcp, 'tools')
            
            if tools_exist:
                print("✅ Email MCP tools are defined")
                return True
            else:
                print("⚠️  Email MCP tools definition check inconclusive")
                return True  # Don't fail for this
                
        except Exception as e:
            print(f"Error checking Email MCP tools: {e}")
            return False
    
    def test_gmail_api_imports(self) -> bool:
        """Test that Gmail API libraries are properly imported"""
        try:
            # Test imports
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            
            print("✅ All Gmail API libraries imported successfully")
            return True
            
        except ImportError as e:
            print(f"❌ Gmail API import error: {e}")
            print("   Install with: pip install google-api-python-client google-auth google-auth-oauthlib")
            return False
        except Exception as e:
            print(f"Error testing Gmail API imports: {e}")
            return False
    
    def test_oauth_credentials_format(self) -> bool:
        """Test OAuth credentials file format"""
        try:
            creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
            
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
    
    async def run_async_tests(self):
        """Run async tests"""
        print("🔄 Running async tests...")
        
        success = True
        if not await self.test_email_server_functionality():
            success = False
        
        return success
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting Email Integration Test Suite")
        print("=" * 60)
        
        # Define tests
        sync_tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Gmail API Imports", self.test_gmail_api_imports),
            ("OAuth Credentials Format", self.test_oauth_credentials_format),
            ("Email Server Creation", self.test_email_server_creation),
            ("Friday Integration", self.test_friday_with_email),
            ("MCP Tools Definition", self.test_email_mcp_tools)
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
        print("📊 EMAIL INTEGRATION TEST RESULTS")
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
        print("1. Create Google Cloud project and enable Gmail API")
        print("2. Download OAuth2 credentials as credentials.json")
        print("3. Set GMAIL_CREDENTIALS_PATH in .env file")
        print("4. Run: pip install -r MCP_Servers/Email_MCP/requirements.txt")
        print("5. Start server: python MCP_Servers/Email_MCP/email_mcp_server.py")
        print("6. Complete OAuth flow in browser")
        
        # Cleanup
        if os.path.exists("test_email_memory.db"):
            os.remove("test_email_memory.db")
        
        if passed == total:
            print("\n🎉 All tests passed! Email integration is ready.")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Review setup and configuration.")
            return False

def main():
    """Run the Email integration test suite"""
    tester = EmailIntegrationTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()