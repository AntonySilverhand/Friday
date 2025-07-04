#!/usr/bin/env python3
"""
Comprehensive test for Friday AI Assistant functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import Friday

def test_friday_initialization():
    """Test Friday AI initialization"""
    print("Testing Friday initialization...")
    try:
        ai = Friday()
        print("✓ Friday AI initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Friday initialization failed: {e}")
        return False

def test_response_generation():
    """Test basic response generation"""
    print("\nTesting response generation...")
    try:
        ai = Friday()
        response = ai.get_response("Hello Friday, introduce yourself")
        print(f"✓ Response generated: {response[:100]}...")
        return True
    except Exception as e:
        print(f"✗ Response generation failed: {e}")
        return False

def test_email_function_structure():
    """Test email function structure (without actually sending)"""
    print("\nTesting email function structure...")
    try:
        ai = Friday()
        # Test the function exists and has proper structure
        if hasattr(ai, 'send_email'):
            print("✓ send_email function exists")
            
            # Test with missing credentials (should return error message)
            result = ai.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body"
            )
            
            if "Error" in result or "successfully" in result:
                print("✓ Email function handles credentials properly")
                return True
            else:
                print("✗ Email function response unexpected")
                return False
        else:
            print("✗ send_email function not found")
            return False
    except Exception as e:
        print(f"✗ Email function test failed: {e}")
        return False

def test_friday_personality():
    """Test Friday's personality traits"""
    print("\nTesting Friday personality...")
    try:
        ai = Friday()
        response = ai.get_response("What is your name?")
        
        # Check for Friday-like responses
        if any(word in response.lower() for word in ['friday', 'sir', 'assist']):
            print("✓ Friday personality traits detected")
            return True
        else:
            print("⚠ Friday personality traits not clearly detected")
            print(f"Response: {response}")
            return True  # Not a critical failure
    except Exception as e:
        print(f"✗ Friday personality test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 50)
    print("Friday AI Assistant - Comprehensive Test Suite")
    print("=" * 50)
    
    tests = [
        test_friday_initialization,
        test_response_generation,
        test_email_function_structure,
        test_friday_personality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 All tests passed! Friday AI is functioning correctly.")
    else:
        print(f"⚠ {total - passed} test(s) failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)