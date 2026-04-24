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


def fetch_manager_picks(team_id, gameweek):
    """Fetch a manager's squad for a given gameweek."""
    url = BASE_URL + f"entry/{team_id}/event/{gameweek}/picks/"
    return fetch_data(url)


def fetch_event_live(gameweek):
    """Fetch live stats for every player in a given gameweek. One call covers all players."""
    url = BASE_URL + f"event/{gameweek}/live/"
    return fetch_data(url)


def build_live_stats_map(event_live_data):
    """
    Turn the /event/{gw}/live/ response into a dict keyed by player id.
    Each value holds total_points, goals_scored, assists for that player.
    """
    stats_map = {}
    if not event_live_data or 'elements' not in event_live_data:
        return stats_map

    for element in event_live_data['elements']:
        player_id = element.get('id')
        stats = element.get('stats', {}) or {}
        stats_map[player_id] = {
            'total_points': stats.get('total_points', 0),
            'goals_scored': stats.get('goals_scored', 0),
            'assists': stats.get('assists', 0),
        }
    return stats_map


def compute_tiebreaker_fields(picks_data, live_stats_map):
    """
    From a manager's picks + the gameweek live-stats map, compute:
      - chip_played (bool): any chip active this GW
      - no_chip_bonus (int): 1 if no chip, 0 if chip (so higher = better, fits reverse=True sort)
      - starters_goals (int): goals by the 11 starters (multiplier > 0)
      - starters_assists (int): assists by the 11 starters
      - captain_points (int): base 1x points of the captain
      - vice_captain_points (int): base 1x points of the vice
      - active_chip (str|None): raw chip name for display
    """
    result = {
        'chip_played': False,
        'no_chip_bonus': 1,
        'starters_goals': 0,
        'starters_assists': 0,
        'captain_points': 0,
        'vice_captain_points': 0,
        'active_chip': None,
    }

    if not picks_data or 'picks' not in picks_data:
        return result

    active_chip = picks_data.get('active_chip')
    result['active_chip'] = active_chip
    result['chip_played'] = active_chip is not None
    result['no_chip_bonus'] = 0 if result['chip_played'] else 1

    for pick in picks_data['picks']:
        player_id = pick.get('element')
        multiplier = pick.get('multiplier', 0)
        stats = live_stats_map.get(player_id, {})
        base_points = stats.get('total_points', 0)
        goals = stats.get('goals_scored', 0)
        assists = stats.get('assists', 0)

        # Starters contribute to goals/assists (bench has multiplier 0).
        # Bench Boost sets bench multipliers to 1, which is exactly what we want —
        # if BB is played, the bench counts as "starters" for this GW.
        if multiplier > 0:
            result['starters_goals'] += goals
            result['starters_assists'] += assists

        if pick.get('is_captain'):
            result['captain_points'] = base_points  # always 1x, regardless of 2x/3x multiplier
        if pick.get('is_vice_captain'):
            result['vice_captain_points'] = base_points  # always 1x

    return result


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

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_manager_gw_data, mgr) for mgr in managers]

        for future in as_completed(futures):
            result = future.result()
            if result:
                leaderboard.append(result)

    print(f"\nCompleted! Processed {processed_count}/{total_managers} managers")

    # Default sort: by net points (descending). Ties are broken later on demand
    # via /tiebreaker for the top 15.
    leaderboard.sort(key=lambda x: x['net_points'], reverse=True)

    return leaderboard, None


def enrich_with_tiebreaker(team_ids, gameweek):
    """
    For the given team_ids (expected: top 15 from the league), fetch picks in parallel,
    fetch event/{gw}/live/ once, and compute tiebreaker fields for each.
    Returns a list of dicts keyed by team_id.
    """
    print(f"\n{'='*80}")
    print(f"Tiebreaker enrichment: GW{gameweek}, {len(team_ids)} managers")
    print(f"{'='*80}\n")

    # One shared call for all per-player stats this GW.
    event_live = fetch_event_live(gameweek)
    live_stats_map = build_live_stats_map(event_live)
    if not live_stats_map:
        print("Warning: empty live stats map — goals/assists/captain points will be 0")

    enriched = {}

    def fetch_and_compute(team_id):
        picks = fetch_manager_picks(team_id, gameweek)
        fields = compute_tiebreaker_fields(picks, live_stats_map)
        return team_id, fields

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_and_compute, tid) for tid in team_ids]
        for future in as_completed(futures):
            try:
                team_id, fields = future.result()
                enriched[team_id] = fields
            except Exception as e:
                print(f"Error in tiebreaker fetch: {e}")

    return enriched


@app.route('/process', methods=['POST'])
def process():
    """Main processing endpoint — returns the full leaderboard sorted by net points."""
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


@app.route('/tiebreaker', methods=['POST'])
def tiebreaker():
    """
    Enrich a list of team_ids (top 15) with tiebreaker data and return them
    re-sorted by the full cascade:
      net_points → no_chip_bonus → goals → assists → captain → vice-captain
    All descending (higher = better; no_chip_bonus is 1 for no-chip, 0 for chip).

    Expected payload: {
      "gameweek": 12,
      "managers": [
        {"team_id": 123, "manager_name": "...", "player_name": "...",
         "gw_points": 70, "transfer_cost": 4, "net_points": 66,
         "total_points": 800, "overall_rank": 1},
        ...
      ]
    }
    """
    try:
        data = request.get_json()
        gameweek = int(data['gameweek'])
        managers = data['managers']

        if not managers:
            return jsonify({'error': 'No managers provided'}), 400

        team_ids = [int(m['team_id']) for m in managers]
        enriched_map = enrich_with_tiebreaker(team_ids, gameweek)

        # Merge enrichment back onto each manager row.
        enriched_managers = []
        for m in managers:
            tid = int(m['team_id'])
            extra = enriched_map.get(tid, {
                'chip_played': False,
                'no_chip_bonus': 1,
                'starters_goals': 0,
                'starters_assists': 0,
                'captain_points': 0,
                'vice_captain_points': 0,
                'active_chip': None,
            })
            merged = {**m, **extra}
            enriched_managers.append(merged)

        # Full tiebreaker cascade. Tuple sort compares left→right.
        enriched_managers.sort(
            key=lambda x: (
                x.get('net_points', 0),
                x.get('no_chip_bonus', 1),
                x.get('starters_goals', 0),
                x.get('starters_assists', 0),
                x.get('captain_points', 0),
                x.get('vice_captain_points', 0),
            ),
            reverse=True,
        )

        print(f"\n{'='*80}")
        print(f"TIEBREAKER SUCCESS! Returning {len(enriched_managers)} enriched managers")
        print(f"{'='*80}\n")

        return jsonify({
            'status': 'completed',
            'gameweek': gameweek,
            'managers': enriched_managers,
        })

    except Exception as e:
        print(f"\nTIEBREAKER ERROR: {str(e)}")
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
