#!/usr/bin/env python3
"""
Standalone Email Test Script
Run this locally to test your SMTP credentials before deploying
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ============================================================================
# CONFIGURE THESE VALUES
# ============================================================================
ALERT_EMAIL = "ashish.tom.work@gmail.com"  # Where to send test email
SMTP_EMAIL = "infinityclaudeuser@gmail.com"  # Gmail account to send from
SMTP_PASSWORD = "your-app-password-here"  # Gmail app password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ============================================================================
# TEST EMAIL FUNCTION
# ============================================================================

def test_email():
    """Test email sending with detailed logging"""
    
    print("=" * 80)
    print("EMAIL TEST SCRIPT")
    print("=" * 80)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check configuration
    print("Configuration:")
    print(f"  To: {ALERT_EMAIL}")
    print(f"  From: {SMTP_EMAIL}")
    print(f"  Password length: {len(SMTP_PASSWORD)} chars")
    print(f"  Server: {SMTP_SERVER}:{SMTP_PORT}")
    print()
    
    if SMTP_PASSWORD == "your-app-password-here":
        print("❌ ERROR: You need to set SMTP_PASSWORD!")
        print()
        print("Get Gmail app password:")
        print("1. Go to: https://myaccount.google.com/apppasswords")
        print("2. Generate new app password")
        print("3. Copy the 16-character password")
        print("4. Replace SMTP_PASSWORD in this script")
        return False
    
    try:
        # Create message
        print("Step 1: Creating email message...")
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = ALERT_EMAIL
        msg['Subject'] = '🧪 FPL Email Test - ' + datetime.now().strftime('%H:%M:%S')
        
        body = f"""
This is a test email from your FPL Leaderboard system.

Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
From: {SMTP_EMAIL}
To: {ALERT_EMAIL}

If you received this email, your SMTP configuration is working correctly! ✅

You can now deploy this configuration to Render.
"""
        msg.attach(MIMEText(body, 'plain'))
        print("✓ Message created")
        print()
        
        # Connect to SMTP server
        print("Step 2: Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        print(f"✓ Connected to {SMTP_SERVER}:{SMTP_PORT}")
        print()
        
        # Start TLS
        print("Step 3: Starting TLS encryption...")
        server.starttls()
        print("✓ TLS encryption enabled")
        print()
        
        # Login
        print("Step 4: Logging in...")
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        print(f"✓ Successfully logged in as {SMTP_EMAIL}")
        print()
        
        # Send message
        print("Step 5: Sending email...")
        server.send_message(msg)
        print("✓ Email sent successfully!")
        print()
        
        # Close connection
        server.quit()
        print("✓ Connection closed")
        print()
        
        print("=" * 80)
        print("✅ SUCCESS!")
        print("=" * 80)
        print(f"Test email sent to: {ALERT_EMAIL}")
        print("Check your inbox (and spam folder)")
        print()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print()
        print("=" * 80)
        print("❌ AUTHENTICATION FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("Common causes:")
        print("1. Wrong app password (not your regular Gmail password)")
        print("2. App password has spaces (remove all spaces)")
        print("3. 2-Factor Authentication not enabled on Gmail")
        print()
        print("Solution:")
        print("1. Enable 2FA: https://myaccount.google.com/security")
        print("2. Generate app password: https://myaccount.google.com/apppasswords")
        print("3. Use the 16-character password (no spaces)")
        return False
        
    except smtplib.SMTPConnectError as e:
        print()
        print("=" * 80)
        print("❌ CONNECTION FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("Possible causes:")
        print("1. Firewall blocking port 587")
        print("2. Wrong SMTP server address")
        print("3. Network connectivity issue")
        print()
        print("Try:")
        print("- Use port 465 instead of 587")
        print("- Check firewall settings")
        return False
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ UNEXPECTED ERROR")
        print("=" * 80)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        return False


if __name__ == "__main__":
    print()
    success = test_email()
    print()
    
    if success:
        print("🎉 Your email configuration is working!")
        print()
        print("Next steps:")
        print("1. Deploy your app to Render")
        print("2. Set these same values in Render environment variables")
        print("3. Email alerts will work automatically")
    else:
        print("⚠️  Fix the errors above, then try again")
    
    print()
