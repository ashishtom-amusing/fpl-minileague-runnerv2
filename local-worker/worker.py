import json
import requests
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

app = Flask(__name__)

BASE_URL = "https://fantasy.premierleague.com/api/"
MAX_WORKERS = 20  # More workers since running locally


def fetch_data(url, timeout=10):
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def fetch_league_data(league_id):
    """Fetch all teams from the league by handling pagination"""
    all_results = []
    page = 1

    while True:
        url = BASE_URL + f"leagues-classic/{league_id}/standings/?page_standings={page}"
        data = fetch_data(url)

        if not data or 'standings' not in data:
            break

        results = data['standings']['results']
        if not results:
            break

        all_results.extend(results)
        print(f"Fetched page {page}: {len(results)} teams")

        if not data['standings'].get('has_next', False):
            break

        page += 1

    if all_results:
        data['standings']['results'] = all_results

    return data


def fetch_manager_history(team_id):
    url = BASE_URL + f"entry/{team_id}/history/"
    return fetch_data(url)


def get_gw_leaderboard(league_id, gameweek):
    """Fetch league data and create leaderboard with parallel processing"""
    print(f"\n{'='*80}")
    print(f"Processing League {league_id}, Gameweek {gameweek}")
    print(f"{'='*80}\n")
    
    league_data = fetch_league_data(league_id)
    
    if not league_data:
        return None, "Failed to fetch league data"
    
    managers = league_data['standings']['results']
    total_managers = len(managers)
    
    print(f"Total managers: {total_managers}")
    print(f"Starting parallel processing with {MAX_WORKERS} workers...\n")
    
    leaderboard = []
    processed_count = 0
    
    # Fetch history for all managers in parallel
    def fetch_manager_gw_data(manager):
        nonlocal processed_count
        try:
            team_id = manager['entry']
            history = fetch_manager_history(team_id)
            
            if history and len(history['current']) >= gameweek:
                gw_points = history['current'][gameweek - 1]['points']
                transfer_cost = history['current'][gameweek - 1]['event_transfers_cost']
                net_points = gw_points - transfer_cost
                
                result = {
                    'manager_name': manager['entry_name'],
                    'player_name': manager['player_name'],
                    'team_id': manager['entry'],
                    'gw_points': gw_points,
                    'transfer_cost': transfer_cost,
                    'net_points': net_points,
                    'total_points': manager['total'],
                    'overall_rank': manager['rank']
                }
                
                processed_count += 1
                if processed_count % 50 == 0:
                    print(f"Progress: {processed_count}/{total_managers} managers processed ({int(processed_count/total_managers*100)}%)")
                
                return result
        except Exception as e:
            print(f"Error processing manager {manager.get('entry')}: {e}")
        
        processed_count += 1
        return None
    
    # Process all managers in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_manager_gw_data, mgr) for mgr in managers]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                leaderboard.append(result)
    
    print(f"\nCompleted! Processed {processed_count}/{total_managers} managers")
    
    leaderboard.sort(key=lambda x: x['gw_points'], reverse=True)
    
    return leaderboard, None


@app.route('/process', methods=['POST'])
def process():
    """Main processing endpoint"""
    try:
        data = request.get_json()
        gameweek = int(data['gameweek'])
        league_id = int(data['league_id'])
        
        print(f"\n{'='*80}")
        print(f"Received request: GW{gameweek}, League {league_id}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        leaderboard_data, error = get_gw_leaderboard(league_id, gameweek)
        
        if error:
            print(f"\nError: {error}")
            return jsonify({'error': error}), 400
        
        result = {
            'status': 'completed',
            'gameweek': gameweek,
            'league_id': league_id,
            'leaderboard': leaderboard_data,
            'total_managers': len(leaderboard_data)
        }
        
        print(f"\n{'='*80}")
        print(f"SUCCESS! Returning {len(leaderboard_data)} managers")
        print(f"{'='*80}\n")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'message': 'Worker server running',
        'max_workers': MAX_WORKERS
    })


if __name__ == '__main__':
    print(f"\n{'='*80}")
    print(f"FPL Worker Server Starting...")
    print(f"Max parallel workers: {MAX_WORKERS}")
    print(f"{'='*80}\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
