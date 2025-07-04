#!/usr/bin/env python3
"""
Test email functionality by sending an email to antonysilverhand@gmail.com
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import Friday

def test_send_email():
    """Test sending an email"""
    print("Testing email sending functionality...")
    
    try:
        ai = Friday()
        
        # Send test email
        result = ai.send_email(
            to="antonysilverhand@gmail.com",
            subject="Friday AI Test Email",
            body="Good day, sir. This is a test email from Friday AI Assistant to verify the email functionality is working properly. All systems are operational."
        )
        
        print(f"Email send result: {result}")
        
        if "successfully" in result:
            print("✓ Email sent successfully!")
            return True
        else:
            print("✗ Email sending failed")
            return False
            
    except Exception as e:
        print(f"✗ Email test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_send_email()
    if success:
        print("\n🎉 Email test completed successfully!")
    else:
        print("\n❌ Email test failed. Check your Gmail credentials in .env file.")
    
    sys.exit(0 if success else 1)