from flask import Flask, render_template, request, jsonify
import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)

# Environment variables
WORKER_URL = os.getenv('WORKER_URL', 'http://localhost:5001')
ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')  # Your email to receive alerts
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')  # Email to send from
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # App password

# Print configuration on startup (without showing full password)
print("=" * 80)
print("CONFIGURATION LOADED:")
print("=" * 80)
print(f"WORKER_URL: {WORKER_URL}")
print(f"ALERT_EMAIL: {ALERT_EMAIL if ALERT_EMAIL else '❌ NOT SET'}")
print(f"SMTP_EMAIL: {SMTP_EMAIL if SMTP_EMAIL else '❌ NOT SET'}")
print(f"SMTP_PASSWORD: {'✓ SET (' + str(len(SMTP_PASSWORD)) + ' chars)' if SMTP_PASSWORD else '❌ NOT SET'}")
print(f"SMTP_SERVER: {SMTP_SERVER}")
print(f"SMTP_PORT: {SMTP_PORT}")
print("=" * 80)


def send_alert_email(error_type, error_message):
    """Send email alert when worker is down"""
    print("\n" + "=" * 80)
    print("EMAIL ALERT TRIGGERED")
    print("=" * 80)
    print(f"Error Type: {error_type}")
    print(f"Error Message: {error_message}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not ALERT_EMAIL:
        print("❌ ALERT_EMAIL is empty - cannot send email")
        print("=" * 80)
        return
    
    if not SMTP_EMAIL:
        print("❌ SMTP_EMAIL is empty - cannot send email")
        print("=" * 80)
        return
        
    if not SMTP_PASSWORD:
        print("❌ SMTP_PASSWORD is empty - cannot send email")
        print("=" * 80)
        return
    
    print(f"✓ All email credentials present")
    print(f"Sending email to: {ALERT_EMAIL}")
    print(f"From: {SMTP_EMAIL}")
    print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
    
    # Send email in background thread to avoid blocking
    import threading
    
    def send_in_background():
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_EMAIL
            msg['To'] = ALERT_EMAIL
            msg['Subject'] = f'🚨 FPL Worker Alert - {error_type}'
            
            body = f"""
FPL Leaderboard Worker Alert
============================

Error Type: {error_type}
Error Message: {error_message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Worker URL: {WORKER_URL}

Action Required:
1. Check if worker.py is running on your local machine
2. Check if ngrok tunnel is active
3. Verify WORKER_URL environment variable matches ngrok URL

To fix:
- Start worker: python worker.py
- Start ngrok: ngrok http 5001
- Update WORKER_URL in Render if ngrok URL changed
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            print(f"Connecting to SMTP server...")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
            print(f"✓ Connected to {SMTP_SERVER}:{SMTP_PORT}")
            
            print(f"Starting TLS...")
            server.starttls()
            print(f"✓ TLS started")
            
            print(f"Logging in as {SMTP_EMAIL}...")
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            print(f"✓ Login successful")
            
            print(f"Sending message...")
            server.send_message(msg)
            print(f"✓ Message sent")
            
            server.quit()
            print(f"✓ Connection closed")
            
            print(f"✅ SUCCESS! Alert email sent to {ALERT_EMAIL}")
            print("=" * 80 + "\n")
            
        except Exception as e:
            print(f"❌ FAILED to send alert email")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("=" * 80 + "\n")
    
    # Start background thread
    print("Starting background email thread...")
    email_thread = threading.Thread(target=send_in_background, daemon=True)
    email_thread.start()
    print("✓ Email thread started (sending in background)")
    print("=" * 80 + "\n")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/status')
def status():
    """Status monitoring page"""
    return render_template('status.html')


@app.route('/leaderboard', methods=['POST'])
def leaderboard():
    """Forward request to worker server"""
    print("\n" + "=" * 80)
    print("LEADERBOARD REQUEST RECEIVED")
    print("=" * 80)
    
    try:
        gameweek = request.form.get('gameweek')
        league_id = request.form.get('league_id')
        
        print(f"Gameweek: {gameweek}")
        print(f"League ID: {league_id}")
        print(f"Forwarding to: {WORKER_URL}/process")
        
        # Forward to worker server
        response = requests.post(
            f'{WORKER_URL}/process',
            json={'gameweek': int(gameweek), 'league_id': int(league_id)},
            timeout=300  # 5 minute timeout
        )
        
        print(f"✓ Worker responded with status: {response.status_code}")
        print("=" * 80 + "\n")
        return jsonify(response.json())
        
    except requests.exceptions.Timeout:
        error_msg = 'Processing timeout after 5 minutes'
        print(f"❌ TIMEOUT: {error_msg}")
        print("Triggering email alert...")
        send_alert_email('Timeout', error_msg)
        print("=" * 80 + "\n")
        return jsonify({'error': 'Processing timeout. Please try again.'}), 504
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f'Cannot connect to worker at {WORKER_URL}'
        print(f"❌ CONNECTION ERROR: {error_msg}")
        print(f"Details: {str(e)}")
        print("Triggering email alert...")
        send_alert_email('Connection Failed', error_msg)
        print("=" * 80 + "\n")
        return jsonify({
            'error': 'Worker server not available. Admin has been notified. Please ensure local worker is running.'
        }), 503
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ UNKNOWN ERROR: {error_msg}")
        print(f"Error type: {type(e).__name__}")
        print("Triggering email alert...")
        send_alert_email('Unknown Error', error_msg)
        print("=" * 80 + "\n")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - checks both UI and worker"""
    ui_status = {'status': 'ok', 'worker_url': WORKER_URL}
    
    # Try to ping worker
    try:
        response = requests.get(f'{WORKER_URL}/health', timeout=5)
        worker_status = response.json()
        ui_status['worker'] = worker_status
        ui_status['worker_reachable'] = True
    except:
        ui_status['worker'] = {'status': 'unreachable'}
        ui_status['worker_reachable'] = False
        ui_status['warning'] = 'Worker server is not responding'
    
    return jsonify(ui_status)


@app.route('/test-email', methods=['GET'])
def test_email():
    """Test endpoint to manually trigger email"""
    print("\n" + "🧪 MANUAL EMAIL TEST TRIGGERED")
    send_alert_email('Test Email', 'This is a manual test of the email system')
    return jsonify({
        'message': 'Email test triggered. Check logs and your inbox.',
        'alert_email': ALERT_EMAIL if ALERT_EMAIL else 'NOT CONFIGURED',
        'smtp_email': SMTP_EMAIL if SMTP_EMAIL else 'NOT CONFIGURED'
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
