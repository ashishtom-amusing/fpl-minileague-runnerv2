from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Environment variables
WORKER_URL = os.getenv('WORKER_URL', 'http://localhost:5001')
DEFAULT_LEAGUE_ID = os.getenv('DEFAULT_LEAGUE_ID', '208271')
FAVORITE_LEAGUES = os.getenv('FAVORITE_LEAGUES', '')  # Comma-separated: "208271:My League,123456:Friends League"

# Print configuration on startup
print("=" * 80)
print("CONFIGURATION LOADED:")
print("=" * 80)
print(f"WORKER_URL: {WORKER_URL}")
print(f"DEFAULT_LEAGUE_ID: {DEFAULT_LEAGUE_ID}")
print(f"FAVORITE_LEAGUES: {FAVORITE_LEAGUES if FAVORITE_LEAGUES else 'Not configured'}")
print("=" * 80)


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
        print("=" * 80 + "\n")
        return jsonify({'error': 'Processing timeout. Please try again.'}), 504
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f'Cannot connect to worker at {WORKER_URL}'
        print(f"❌ CONNECTION ERROR: {error_msg}")
        print(f"Details: {str(e)}")
        print("=" * 80 + "\n")
        return jsonify({
            'error': 'Worker server not available. Please check the status page and contact the developer if the issue persists.'
        }), 503
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ UNKNOWN ERROR: {error_msg}")
        print(f"Error type: {type(e).__name__}")
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


@app.route('/favorite-leagues', methods=['GET'])
def favorite_leagues():
    """Return list of favorite leagues"""
    leagues = []
    
    # Always add default league
    leagues.append({
        'id': DEFAULT_LEAGUE_ID,
        'name': f'Default League ({DEFAULT_LEAGUE_ID})'
    })
    
    # Parse and add configured favorite leagues
    if FAVORITE_LEAGUES:
        try:
            for league in FAVORITE_LEAGUES.split(','):
                league = league.strip()
                if ':' in league:
                    league_id, league_name = league.split(':', 1)
                    leagues.append({
                        'id': league_id.strip(),
                        'name': league_name.strip()
                    })
        except Exception as e:
            print(f"Error parsing FAVORITE_LEAGUES: {e}")
    
    return jsonify(leagues)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
