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


def send_alert_email(error_type, error_message):
    """Send email alert when worker is down"""
    if not ALERT_EMAIL or not SMTP_EMAIL or not SMTP_PASSWORD:
        print("Email alerts not configured - skipping")
        return
    
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
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Alert email sent to {ALERT_EMAIL}")
        
    except Exception as e:
        print(f"Failed to send alert email: {e}")


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
    try:
        gameweek = request.form.get('gameweek')
        league_id = request.form.get('league_id')
        
        # Forward to worker server
        response = requests.post(
            f'{WORKER_URL}/process',
            json={'gameweek': int(gameweek), 'league_id': int(league_id)},
            timeout=300  # 5 minute timeout
        )
        
        return jsonify(response.json())
        
    except requests.exceptions.Timeout:
        error_msg = 'Processing timeout after 5 minutes'
        send_alert_email('Timeout', error_msg)
        return jsonify({'error': 'Processing timeout. Please try again.'}), 504
        
    except requests.exceptions.ConnectionError:
        error_msg = f'Cannot connect to worker at {WORKER_URL}'
        send_alert_email('Connection Failed', error_msg)
        return jsonify({
            'error': 'Worker server not available. Admin has been notified. Please ensure local worker is running.'
        }), 503
        
    except Exception as e:
        error_msg = str(e)
        send_alert_email('Unknown Error', error_msg)
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
