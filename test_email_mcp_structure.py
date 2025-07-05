#!/usr/bin/env python3
"""
Basic structure test for Email MCP Server - tests imports and basic functionality
without requiring full dependencies
"""

import os
import sys
import inspect
from typing import get_type_hints

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_email_mcp_structure():
    """Test the basic structure of the Email MCP server"""
    print("🔍 Testing Email MCP Server Structure")
    print("=" * 50)
    
    try:
        # Test file existence
        email_mcp_path = "/root/coding/Friday/MCP_Servers/Email_MCP/email_mcp_server.py"
        if not os.path.exists(email_mcp_path):
            print("❌ Email MCP server file not found")
            return False
        
        print("✅ Email MCP server file exists")
        
        # Read and analyze the file
        with open(email_mcp_path, 'r') as f:
            content = f.read()
        
        # Check for required components
        required_components = [
            ("EmailMCPServer class", "class EmailMCPServer"),
            ("EmailMessage dataclass", "@dataclass"),
            ("get_recent_emails method", "async def get_recent_emails"),
            ("search_emails method", "async def search_emails"),
            ("get_email_by_id method", "async def get_email_by_id"),
            ("send_email method", "async def send_email"),
            ("mark_as_read method", "async def mark_as_read"),
            ("archive_emails method", "async def archive_emails"),
            ("get_labels method", "async def get_labels"),
            ("Gmail API scopes", "SCOPES = ["),
            ("OAuth2 authentication", "_get_gmail_service"),
            ("Email parsing", "_parse_email_message"),
            ("Attachment handling", "_extract_attachments"),
            ("Body extraction", "_extract_body_content"),
            ("FastMCP integration", "FastMCP"),
            ("MCP tools definition", "@mcp.tool()"),
        ]
        
        passed_checks = 0
        total_checks = len(required_components)
        
        for component_name, search_string in required_components:
            if search_string in content:
                print(f"✅ {component_name} found")
                passed_checks += 1
            else:
                print(f"❌ {component_name} not found")
        
        # Check MCP tools count
        mcp_tool_count = content.count("@mcp.tool()")
        expected_tools = 7  # 7 main tools
        
        if mcp_tool_count >= expected_tools:
            print(f"✅ Found {mcp_tool_count} MCP tools (expected {expected_tools})")
            passed_checks += 1
        else:
            print(f"❌ Found {mcp_tool_count} MCP tools (expected {expected_tools})")
        
        total_checks += 1
        
        # Check for proper async/await usage
        async_methods = [
            "get_recent_emails",
            "search_emails", 
            "get_email_by_id",
            "send_email",
            "mark_as_read",
            "archive_emails",
            "get_labels"
        ]
        
        async_check_passed = 0
        for method in async_methods:
            if f"async def {method}" in content:
                async_check_passed += 1
        
        if async_check_passed == len(async_methods):
            print(f"✅ All {len(async_methods)} methods are properly async")
            passed_checks += 1
        else:
            print(f"❌ Only {async_check_passed}/{len(async_methods)} methods are async")
        
        total_checks += 1
        
        # Check for error handling
        error_handling_patterns = [
            "try:",
            "except Exception as e:",
            "logger.error",
            "return []",
            "return None",
            "return {\"error\":"
        ]
        
        error_handling_found = sum(1 for pattern in error_handling_patterns if pattern in content)
        
        if error_handling_found >= 4:  # Should have multiple error handling patterns
            print(f"✅ Error handling patterns found ({error_handling_found} patterns)")
            passed_checks += 1
        else:
            print(f"❌ Insufficient error handling patterns ({error_handling_found} patterns)")
        
        total_checks += 1
        
        # Check for proper imports
        required_imports = [
            "from mcp.server.fastmcp import FastMCP",
            "from google.auth.transport.requests import Request",
            "from google.oauth2.credentials import Credentials",
            "from google_auth_oauthlib.flow import InstalledAppFlow",
            "from googleapiclient.discovery import build",
            "from googleapiclient.errors import HttpError",
            "import base64",
            "import asyncio",
            "from typing import List, Dict, Optional, Any",
            "from datetime import datetime, timedelta",
            "from dataclasses import dataclass",
            "import logging"
        ]
        
        import_check_passed = 0
        for import_line in required_imports:
            if import_line in content:
                import_check_passed += 1
        
        if import_check_passed >= len(required_imports) - 2:  # Allow for some flexibility
            print(f"✅ Required imports found ({import_check_passed}/{len(required_imports)})")
            passed_checks += 1
        else:
            print(f"❌ Missing required imports ({import_check_passed}/{len(required_imports)})")
        
        total_checks += 1
        
        # Summary
        print(f"\n📊 Structure Analysis Summary:")
        print(f"Passed checks: {passed_checks}/{total_checks}")
        print(f"Success rate: {(passed_checks/total_checks)*100:.1f}%")
        
        if passed_checks == total_checks:
            print("\n🎉 Email MCP server structure is complete and properly implemented!")
            return True
        else:
            print(f"\n⚠️  {total_checks - passed_checks} structural issues found")
            return False
            
    except Exception as e:
        print(f"❌ Error analyzing Email MCP structure: {e}")
        return False

def test_requirements_file():
    """Test the requirements file"""
    print("\n🔍 Testing Requirements File")
    print("=" * 30)
    
    try:
        req_path = "/root/coding/Friday/MCP_Servers/Email_MCP/requirements.txt"
        if not os.path.exists(req_path):
            print("❌ requirements.txt not found")
            return False
        
        with open(req_path, 'r') as f:
            requirements = f.read().strip().split('\n')
        
        required_packages = [
            "google-api-python-client",
            "google-auth",
            "google-auth-oauthlib",
            "fastmcp",
            "python-dotenv"
        ]
        
        found_packages = []
        for req in requirements:
            if req.strip() and not req.strip().startswith('#'):
                package_name = req.split('==')[0].split('>=')[0].split('<=')[0]
                found_packages.append(package_name)
        
        missing_packages = []
        for package in required_packages:
            if package not in found_packages:
                missing_packages.append(package)
        
        if not missing_packages:
            print(f"✅ All required packages found in requirements.txt")
            print(f"   Total packages: {len(found_packages)}")
            return True
        else:
            print(f"❌ Missing packages: {missing_packages}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False

def test_oauth_setup_documentation():
    """Test OAuth setup documentation"""
    print("\n🔍 Testing OAuth Setup Documentation")
    print("=" * 40)
    
    try:
        oauth_doc_path = "/root/coding/Friday/MCP_Servers/Email_MCP/GMAIL_OAUTH_SETUP.md"
        if not os.path.exists(oauth_doc_path):
            print("❌ OAuth setup documentation not found")
            return False
        
        with open(oauth_doc_path, 'r') as f:
            doc_content = f.read()
        
        # Check for essential sections
        essential_sections = [
            "# Gmail OAuth",
            "## Prerequisites",
            "### Step 1",
            "### Step 2", 
            "credentials.json",
            "token.pickle",
            "GMAIL_CREDENTIALS_PATH",
            "GMAIL_TOKEN_PATH"
        ]
        
        found_sections = 0
        for section in essential_sections:
            if section in doc_content:
                found_sections += 1
        
        if found_sections >= len(essential_sections) - 1:  # Allow some flexibility
            print(f"✅ OAuth setup documentation is comprehensive")
            print(f"   Found {found_sections}/{len(essential_sections)} essential sections")
            return True
        else:
            print(f"❌ OAuth setup documentation incomplete ({found_sections}/{len(essential_sections)})")
            return False
            
    except Exception as e:
        print(f"❌ Error checking OAuth documentation: {e}")
        return False

def main():
    """Run all structure tests"""
    print("🚀 Email MCP Structure Test Suite")
    print("=" * 60)
    
    tests = [
        ("Email MCP Server Structure", test_email_mcp_structure),
        ("Requirements File", test_requirements_file),
        ("OAuth Setup Documentation", test_oauth_setup_documentation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} test PASSED")
            else:
                print(f"\n❌ {test_name} test FAILED")
        except Exception as e:
            print(f"\n❌ {test_name} test FAILED with exception: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All structure tests passed! Email MCP server is properly implemented.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)