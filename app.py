import os
import requests
from flask import Flask, jsonify, render_template
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MBTA API Configuration
MBTA_API_BASE = "https://api-v3.mbta.com"
MBTA_API_KEY = os.getenv('MBTA_API_KEY')  # Optional - you can use without key for testing

# How many upcoming predictions to show (configurable via env)
MAX_PREDICTIONS = int(os.getenv('MAX_PREDICTIONS', '6'))

# Walk times and wait times for inbound/outbound (configurable via env)
INBOUND_WALK_TIME = int(os.getenv('INBOUND_WALK_TIME', '3'))
OUTBOUND_WALK_TIME = int(os.getenv('OUTBOUND_WALK_TIME', '3'))
INBOUND_MAX_WAIT = int(os.getenv('INBOUND_MAX_WAIT', '5'))
OUTBOUND_MAX_WAIT = int(os.getenv('OUTBOUND_MAX_WAIT', '5'))

# Route 39 ID and Bynner Street stop ID
ROUTE_39_ID = "39"
# Bynner Street stop ID - using a known working stop ID for Route 39
# This is the inbound stop at Bynner St
BYNNER_STREET_STOP_ID = "1835"  # Fallback stop ID

# Use US Eastern time for display and morning/evening switching
EASTERN = ZoneInfo("America/New_York")

def get_mbta_headers():
    """Get headers for MBTA API requests"""
    headers = {
        'Accept': 'application/vnd.api+json'
    }
    if MBTA_API_KEY:
        headers['X-API-Key'] = MBTA_API_KEY
    return headers

def find_stop_ids_by_name():
    """Find the stop IDs for Bynner Street (inbound) and 677 Huntington Ave (outbound) on route 39"""
    stops = {'inbound': {'id': None, 'name': None}, 'outbound': {'id': None, 'name': None}}
    
    # Inbound: Bynner Street (direction_id=1)
    try:
        url = f"{MBTA_API_BASE}/stops"
        params = {
            'filter[route]': ROUTE_39_ID,
            'filter[direction_id]': '1',  # Inbound
        }
        
        response = requests.get(url, params=params, headers=get_mbta_headers())
        response.raise_for_status()
        
        data = response.json()
        
        # Look for Bynner Street in the inbound stops
        for stop in data.get('data', []):
            stop_name_api = stop['attributes']['name']
            if 'Bynner' in stop_name_api:
                stops['inbound']['id'] = stop['id']
                stops['inbound']['name'] = stop_name_api
                break
    
    except requests.RequestException as e:
        print(f"Error finding inbound stop: {e}")
    
    # Outbound: 677 Huntington Ave (direction_id=0)
    try:
        url = f"{MBTA_API_BASE}/stops"
        params = {
            'filter[route]': ROUTE_39_ID,
            'filter[direction_id]': '0',  # Outbound
        }
        
        response = requests.get(url, params=params, headers=get_mbta_headers())
        response.raise_for_status()
        
        data = response.json()
        
        # Look for Huntington Ave in the outbound stops
        for stop in data.get('data', []):
            stop_name_api = stop['attributes']['name']
            if '677' in stop_name_api:
                stops['outbound']['id'] = stop['id']
                stops['outbound']['name'] = stop_name_api
                break
    
    except requests.RequestException as e:
        print(f"Error finding outbound stop: {e}")
    
    return stops

def get_next_bus_predictions(stop_id, direction_id, walk_time=3, max_wait=5):
    """Get real-time predictions for the next 39 bus at the specified stop"""
    try:
        url = f"{MBTA_API_BASE}/predictions"
        params = {
            'filter[stop]': stop_id,
            'filter[route]': ROUTE_39_ID,
            'filter[direction_id]': direction_id,
            'sort': 'arrival_time',
            'include': 'trip,vehicle,route'
        }
        
        response = requests.get(url, params=params, headers=get_mbta_headers())
        response.raise_for_status()
        
        data = response.json()
        predictions = []
        
        # Create lookup for included data (trips, vehicles, routes)
        included_lookup = {}
        for item in data.get('included', []):
            included_lookup[f"{item['type']}-{item['id']}"] = item
        
        for prediction in data.get('data', []):
            attributes = prediction['attributes']
            relationships = prediction.get('relationships', {})
            
            # Get arrival time
            arrival_time = attributes.get('arrival_time')
            departure_time = attributes.get('departure_time')
            
            # Use arrival time if available, otherwise departure time
            predicted_time = arrival_time or departure_time
            
            if predicted_time:
                pred_datetime = datetime.fromisoformat(predicted_time.replace('Z', '+00:00'))
                now = datetime.now(pred_datetime.tzinfo)
                minutes_away = int((pred_datetime - now).total_seconds() / 60)
                
                # Calculate optimal leave time using provided walk_time and max_wait
                # To arrive 2.5 min early (middle of acceptable 0-max_wait min wait window)
                optimal_arrival_buffer = max_wait / 2.0
                time_to_leave_minutes = int(max(0, minutes_away - walk_time - optimal_arrival_buffer))
                
                # Determine if bus is catchable
                can_catch_bus = minutes_away > walk_time
                
                # Get additional info from relationships
                trip_info = None
                vehicle_info = None
                
                # Get trip information
                if 'trip' in relationships and relationships['trip']['data']:
                    trip_id = relationships['trip']['data']['id']
                    trip_info = included_lookup.get(f"trip-{trip_id}")
                
                # Get vehicle information
                if 'vehicle' in relationships and relationships['vehicle']['data']:
                    vehicle_id = relationships['vehicle']['data']['id']
                    vehicle_info = included_lookup.get(f"vehicle-{vehicle_id}")
                
                # Extract useful information
                headsign = trip_info['attributes']['headsign'] if trip_info else 'Forest Hills'
                vehicle_label = vehicle_info['attributes']['label'] if vehicle_info else None
                
                # Get status - fix the None issue
                status = attributes.get('status')
                if not status or status is None:
                    if minutes_away <= 1:
                        status = 'Arriving'
                    elif minutes_away <= 5:
                        status = 'Approaching'
                    else:
                        status = 'On time'
                
                predictions.append({
                    'arrival_time': predicted_time,
                    'minutes_away': minutes_away,
                    'time_to_leave_minutes': time_to_leave_minutes,
                    'can_catch_bus': can_catch_bus,
                    'formatted_time': pred_datetime.strftime('%I:%M %p'),
                    'status': status,
                    'headsign': headsign,
                    'vehicle_label': vehicle_label,
                    'delay_seconds': attributes.get('delay', 0)
                })
        
        return predictions[:MAX_PREDICTIONS]  # Return next N predictions
        
    except requests.RequestException as e:
        print(f"Error getting predictions: {e}")
        return []

@app.route('/')
def index():
    """Main page showing next bus arrivals"""
    try:
        # Find stop IDs for both directions
        stops = find_stop_ids_by_name()
        
        # Get predictions for both directions with their specific walk times and wait times
        inbound_predictions = []
        outbound_predictions = []
        
        if stops['inbound']['id']:
            inbound_predictions = get_next_bus_predictions(stops['inbound']['id'], '1', INBOUND_WALK_TIME, INBOUND_MAX_WAIT)
        
        if stops['outbound']['id']:
            outbound_predictions = get_next_bus_predictions(stops['outbound']['id'], '0', OUTBOUND_WALK_TIME, OUTBOUND_MAX_WAIT)
        
        # Calculate buses arriving within 30 minutes
        inbound_count_30min = sum(1 for pred in inbound_predictions if pred['minutes_away'] <= 30)
        outbound_count_30min = sum(1 for pred in outbound_predictions if pred['minutes_away'] <= 30)
        
        # Determine time of day: morning (before noon) or afternoon in Eastern time
        current_hour = datetime.now(EASTERN).hour
        is_morning = current_hour < 12
        current_time = datetime.now(EASTERN).strftime('%I:%M:%S %p')
        
        # Use inbound stop name as primary
        inbound_stop_name = stops['inbound']['name'] or "Bynner Street (Route 39)"
        outbound_stop_name = stops['outbound']['name'] or "677 Huntington Ave (Route 39)"
        
        return render_template(
            'index.html',
            inbound_predictions=inbound_predictions,
            outbound_predictions=outbound_predictions,
            inbound_count_30min=inbound_count_30min,
            outbound_count_30min=outbound_count_30min,
            inbound_stop_name=inbound_stop_name,
            outbound_stop_name=outbound_stop_name,
            is_morning=is_morning,
            current_time=current_time
        )
    except Exception as e:
        # Return error page if something goes wrong
        error_html = f"""
        <html>
        <body>
            <h1>Error Loading Bus Tracker</h1>
            <p>Error: {str(e)}</p>
            <p><a href="/">Try Again</a></p>
        </body>
        </html>
        """
        return error_html, 500

@app.route('/api/predictions')
def api_predictions():
    """API endpoint returning JSON predictions"""
    stops = find_stop_ids_by_name()
    
    # Get predictions for both directions
    inbound_predictions = []
    outbound_predictions = []
    
    if stops['inbound']['id']:
        inbound_predictions = get_next_bus_predictions(stops['inbound']['id'], '1')
    
    if stops['outbound']['id']:
        outbound_predictions = get_next_bus_predictions(stops['outbound']['id'], '0')
    
    # Use inbound stop name as primary
    stop_name = stops['inbound']['name'] or stops['outbound']['name'] or "Bynner Street (estimated)"
    
    return jsonify({
        'stop_name': stop_name,
        'route': '39',
        'directions': {
            'inbound': {
                'stop_id': stops['inbound']['id'],
                'stop_name': stops['inbound']['name'],
                'predictions': inbound_predictions
            },
            'outbound': {
                'stop_id': stops['outbound']['id'],
                'stop_name': stops['outbound']['name'],
                'predictions': outbound_predictions
            }
        },
        'last_updated': datetime.now().isoformat()
    })

@app.route('/debug-predictions')
def debug_predictions():
    """Debug endpoint to see raw prediction data"""
    try:
        stops = find_stop_ids_by_name()
        stop_id = stops['inbound']['id'] or BYNNER_STREET_STOP_ID
        stop_name = stops['inbound']['name'] or "Bynner Street (Route 39)"
        
        # Get raw API response for inbound
        url = f"{MBTA_API_BASE}/predictions"
        params = {
            'filter[stop]': stop_id,
            'filter[route]': ROUTE_39_ID,
            'filter[direction_id]': '1',
            'sort': 'arrival_time',
            'include': 'trip,vehicle,route'
        }
        
        # Get raw API response
        url = f"{MBTA_API_BASE}/predictions"
        params = {
            'filter[stop]': stop_id,
            'filter[route]': ROUTE_39_ID,
            'filter[direction_id]': '1',
            'sort': 'arrival_time',
            'include': 'trip,vehicle,route'
        }
        
        response = requests.get(url, params=params, headers=get_mbta_headers())
        
        if response.status_code == 200:
            data = response.json()
            
            # Process first prediction for detailed info
            debug_info = {
                'stop_id': stop_id,
                'stop_name': stop_name,
                'raw_predictions_count': len(data.get('data', [])),
                'raw_first_prediction': data.get('data', [{}])[0] if data.get('data') else None,
                'included_data': data.get('included', []),
                'response_status': response.status_code
            }
            
            return jsonify(debug_info)
        else:
            return jsonify({
                'error': f"API returned {response.status_code}",
                'response_text': response.text
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("Starting MBTA Route 39 Bus Tracker...")
    print(f"MBTA API Key configured: {'Yes' if MBTA_API_KEY else 'No (using rate-limited access)'}")
    
    # Try to find the correct stop IDs on startup
    stops = find_stop_ids_by_name()
    if stops['inbound']['id']:
        print(f"Found inbound stop: {stops['inbound']['name']} (ID: {stops['inbound']['id']})")
    else:
        print(f"Using fallback inbound stop ID: {BYNNER_STREET_STOP_ID}")
    
    if stops['outbound']['id']:
        print(f"Found outbound stop: {stops['outbound']['name']} (ID: {stops['outbound']['id']})")
    else:
        print("Outbound stop ID not found - outbound predictions may not work")
    
    app.run(host='0.0.0.0', port=5000, debug=False)