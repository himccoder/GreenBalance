#!/usr/bin/env python3
"""
Simple Flask app to test HAProxy Dataplane API weight changes with WattTime integration
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional
import random
import math
from dotenv import load_dotenv
from simple_data_processor import get_simulation_engine

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'test_secret_key'

# Historical Simulation Engine (singleton)
simulation_engine = get_simulation_engine()

# Dataplane API configuration
DATAPLANE_HOST = "haproxy"  # Use container name for Docker networking
DATAPLANE_PORT = 5555
DATAPLANE_USER = "admin"
DATAPLANE_PASS = "password"
BACKEND_NAME = "local_servers"

# HAProxy Stats configuration
HAPROXY_STATS_URL = "http://haproxy:8404/stats"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WattTimeAPI:
    """Handles all interactions with the WattTime API"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.token = None
        self.base_url = "https://api.watttime.org"
    
    def login(self) -> bool:
        """Authenticate with WattTime API and get access token"""
        try:
            login_url = f"{self.base_url}/login"
            response = requests.get(
                login_url, 
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=10
            )
            response.raise_for_status()
            
            self.token = response.json().get('token')
            if self.token:
                logger.info("Successfully authenticated with WattTime API")
                return True
            else:
                logger.error("No token received from WattTime API")
                return False
                
        except Exception as e:
            logger.error(f"Failed to authenticate with WattTime API: {e}")
            return False
    
    def get_carbon_intensity(self, region: str, base_intensity: Optional[float] = None) -> Optional[float]:
        """Get carbon intensity for a region"""
        if not self.token:
            if not self.login():
                return None
        
        try:
            # For CAISO_NORTH, use real WattTime data
            if region == "CAISO_NORTH":
                return self._get_real_intensity(region)
            else:
                # For other regions, use simulated data
                if base_intensity is None:
                    base_intensity = 600.0  # Default baseline
                return self._get_simulated_intensity(base_intensity)
                
        except Exception as e:
            logger.error(f"Error getting carbon intensity for {region}: {e}")
            return None
    
    def _get_real_intensity(self, region: str) -> Optional[float]:
        """Get real carbon intensity data from WattTime"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            url = f"{self.base_url}/v3/signal-index"
            params = {
                'region': region,
                'signal_type': 'co2_moer'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                intensity = data['data'][0]['value']
                logger.info(f"🌱 REAL carbon intensity for {region}: {intensity:.2f} lbs CO2/MWh")
                return intensity
            else:
                logger.warning(f"No carbon intensity data available for {region}")
                return 600.0  # Fallback value
                
        except Exception as e:
            logger.error(f"Failed to get real carbon intensity for {region}: {e}")
            return 600.0  # Fallback value
    
    def _get_simulated_intensity(self, base_intensity: float) -> float:
        """Generate realistic simulated carbon intensity data"""
        # Add time-based variation (lower at night, higher during peak hours)
        hour = datetime.now().hour
        time_factor = 0.8 + 0.4 * math.sin((hour - 6) * math.pi / 12)
        
        # Add random variation (±20%)
        random_factor = 1 + (random.random() - 0.5) * 0.4
        
        # Calculate final intensity
        intensity = base_intensity * time_factor * random_factor
        
        # Ensure reasonable bounds (200-1000 lbs CO2/MWh)
        intensity = max(200, min(1000, intensity))
        
        logger.info(f"🤖 SIMULATED carbon intensity: {intensity:.2f} lbs CO2/MWh")
        return intensity

class DataplaneAPI:
    def __init__(self):
        self.base_url = f"http://{DATAPLANE_HOST}:{DATAPLANE_PORT}"
        self.auth = HTTPBasicAuth(DATAPLANE_USER, DATAPLANE_PASS)
    
    def get_servers(self):
        """Get current server configurations"""
        try:
            url = f"{self.base_url}/v2/services/haproxy/configuration/servers"
            params = {"backend": BACKEND_NAME}
            response = requests.get(url, auth=self.auth, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            return None
        except Exception as e:
            print(f"Error getting servers: {e}")
            return None
    
    def get_version(self):
        """Get current configuration version"""
        try:
            url = f"{self.base_url}/v2/services/haproxy/configuration/version"
            response = requests.get(url, auth=self.auth, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting version: {e}")
            return None
    
    def change_server_weight(self, server_name, new_weight):
        """Change weight for a specific server"""
        try:
            # Get current config version
            version = self.get_version() #This is the version of the configuration
            if not version:
                return False, "Could not get configuration version"
            
            # Get current server config
            url = f"{self.base_url}/v2/services/haproxy/configuration/servers/{server_name}"
            params = {"backend": BACKEND_NAME}
            response = requests.get(url, auth=self.auth, params=params, timeout=5)
            
            if response.status_code != 200:
                return False, f"Could not get current server config: {response.status_code}"
            
            current_config = response.json()["data"]
            
            # Update weight
            updated_config = current_config.copy()
            updated_config["weight"] = int(new_weight)
            
            # Send PUT request
            put_params = {"backend": BACKEND_NAME, "version": version}
            put_response = requests.put(
                url, 
                auth=self.auth, 
                params=put_params,
                json=updated_config,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if put_response.status_code in [200, 202]:  # 200 OK or 202 Accepted
                return True, f"Successfully changed {server_name} weight to {new_weight}"
            else:
                return False, f"Failed to change weight: {put_response.status_code} - {put_response.text}"
                
        except Exception as e:
            return False, f"Error changing weight: {e}"

# Initialize API clients
api = DataplaneAPI()

# Initialize WattTime API
watttime_username = os.getenv('WATTTIME_USERNAME')
watttime_password = os.getenv('WATTTIME_PASSWORD')

watttime_api = None
if watttime_username and watttime_password:
    try:
        watttime_api = WattTimeAPI(watttime_username, watttime_password)
        print("🌱 WattTime API initialized - Carbon features enabled")
    except Exception as e:
        print(f"⚠️ WattTime API initialization failed: {e}")
else:
    print("⚠️ WattTime credentials not found - Using demo carbon data")

# Server to region mapping (matching your main controller)
server_regions = {
    'n1': {'region': 'CAISO_NORTH', 'name': 'US West (California)', 'type': 'real'},
    'n2': {'region': 'ERCOT', 'name': 'US Central (Texas)', 'base_intensity': 500, 'type': 'simulated'},
    'n3': {'region': 'PJM', 'name': 'US East (Mid-Atlantic)', 'base_intensity': 700, 'type': 'simulated'}
}

def calculate_green_weights(carbon_intensities: Dict[str, float]) -> Dict[str, int]:
    """Calculate server weights based on carbon intensity (lower carbon = higher weight)"""
    
    # Convert carbon intensities to "green scores" (inverted)
    green_scores = {}
    for server, intensity in carbon_intensities.items():
        # Invert: lower carbon intensity = higher green score
        green_scores[server] = 1000.0 / intensity
    
    # Find min and max scores for normalization
    min_score = min(green_scores.values())
    max_score = max(green_scores.values())
    score_range = max_score - min_score
    
    # Convert to HAProxy weights (1-256)
    weights = {}
    for server, score in green_scores.items():
        if score_range > 0:
            # Normalize to 0-1, then scale to 50-256 (ensuring minimum traffic)
            normalized = (score - min_score) / score_range
            weight = int(50 + normalized * 206)  # 50-256 range
        else:
            weight = 150  # Equal weights if all scores are the same
        
        weights[server] = weight
    
    return weights

def get_carbon_intensities():
    """Get current carbon intensities for all regions"""
    carbon_data = {}
    
    if not watttime_api:
        # Return mock data if WattTime not available
        return {
            'n1': {'intensity': 450.0, 'type': 'mock', 'region': 'CAISO_NORTH'},
            'n2': {'intensity': 550.0, 'type': 'mock', 'region': 'ERCOT'},
            'n3': {'intensity': 650.0, 'type': 'mock', 'region': 'PJM'}
        }
    
    for server_id, config in server_regions.items():
        region = config['region']
        base_intensity = config.get('base_intensity')
        
        intensity = watttime_api.get_carbon_intensity(region, base_intensity)
        if intensity is not None:
            carbon_data[server_id] = {
                'intensity': intensity,
                'type': config['type'],
                'region': region,
                'name': config['name']
            }
        else:
            # Fallback values
            carbon_data[server_id] = {
                'intensity': 600.0,
                'type': 'fallback',
                'region': region,
                'name': config['name']
            }
    
    return carbon_data

@app.route('/')
def index():
    """Main page showing current server weights and carbon intensities"""
    servers = api.get_servers()
    if servers is None:
        flash("❌ Could not connect to HAProxy Dataplane API", "error")
        servers = []
    
    # Get carbon intensity data
    carbon_data = get_carbon_intensities()
    
    # Calculate total weight and percentages
    total_weight = sum(server['weight'] for server in servers)
    for server in servers:
        server['percentage'] = (server['weight'] / total_weight * 100) if total_weight > 0 else 0
        
        # Add carbon data to server info
        if server['name'] in carbon_data:
            server['carbon'] = carbon_data[server['name']]
        else:
            server['carbon'] = {'intensity': 'N/A', 'type': 'unknown', 'region': 'Unknown'}
    
    return render_template('index.html', 
                         servers=servers, 
                         backend=BACKEND_NAME, 
                         watttime_available=watttime_api is not None,
                         carbon_data=carbon_data)

@app.route('/change_weight', methods=['POST'])
def change_weight():
    """Handle weight change requests"""
    server_name = request.form.get('server_name')
    new_weight = request.form.get('new_weight')
    
    if not server_name or not new_weight:
        flash("❌ Server name and weight are required", "error")
        return redirect(url_for('index'))
    
    try:
        new_weight = int(new_weight)
        if new_weight < 1 or new_weight > 256:
            flash("❌ Weight must be between 1 and 256", "error")
            return redirect(url_for('index'))
    except ValueError:
        flash("❌ Weight must be a valid number", "error")
        return redirect(url_for('index'))
    
    success, message = api.change_server_weight(server_name, new_weight)
    
    if success:
        flash(f"✅ {message}", "success")
    else:
        flash(f"❌ {message}", "error")
    
    return redirect(url_for('index'))

@app.route('/api/servers')
def api_servers():
    """API endpoint to get current servers as JSON"""
    servers = api.get_servers()
    if servers is None:
        return jsonify({"error": "Could not get servers"}), 500
    return jsonify({"servers": servers, "backend": BACKEND_NAME})

@app.route('/api/server-weights')
def get_server_weights():
    """API endpoint to get current server weights for real-time updates"""
    servers = api.get_servers()
    if not servers:
        return jsonify({'success': False, 'error': 'Could not connect to HAProxy'})
    
    # Calculate percentages
    total_weight = sum(server['weight'] for server in servers)
    for server in servers:
        server['percentage'] = (server['weight'] / total_weight * 100) if total_weight > 0 else 0
    
    # Find server with highest weight
    leader = max(servers, key=lambda s: s['weight']) if servers else None
    
    return jsonify({
        'success': True,
        'servers': servers,
        'leader': leader['name'] if leader else None,
        'total_weight': total_weight,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/carbon/update')
def update_carbon_weights():
    """Update server weights based on current carbon intensities"""
    if not watttime_api:
        error_msg = "❌ WattTime API not available - cannot update carbon-based weights"
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'error': error_msg})
        flash(error_msg, "error")
        return redirect(url_for('index'))
    
    try:
        # Get current carbon intensities
        carbon_data = get_carbon_intensities()
        carbon_intensities = {server_id: data['intensity'] for server_id, data in carbon_data.items()}
        
        # Calculate green weights
        weights = calculate_green_weights(carbon_intensities)
        
        # Update server weights
        success_count = 0
        failed_servers = []
        for server_name, weight in weights.items():
            success, message = api.change_server_weight(server_name, weight)
            if success:
                success_count += 1
            else:
                failed_servers.append(f"{server_name}: {message}")
        
        # Prepare response data
        carbon_updates = []
        for server_id, weight in weights.items():
            carbon_info = carbon_data[server_id]
            intensity = carbon_info['intensity']
            region_name = carbon_info['name']
            carbon_updates.append({
                'server': server_id,
                'region': region_name,
                'intensity': intensity,
                'weight': weight
            })
        
        if request.headers.get('Accept') == 'application/json':
            # Return JSON response for AJAX requests
            if success_count == len(weights):
                return jsonify({
                    'success': True,
                    'message': '🌱 Applied carbon-based weights successfully! Lower carbon = higher weight',
                    'updates': carbon_updates,
                    'total_updated': success_count
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'⚠️ Partially applied carbon weights: {success_count}/{len(weights)} servers updated',
                    'updates': carbon_updates,
                    'errors': failed_servers,
                    'total_updated': success_count
                })
        else:
            # Traditional flash message redirect
            if success_count == len(weights):
                flash(f"🌱 Applied carbon-based weights successfully! Lower carbon = higher weight", "success")
                
                # Show the carbon summary
                for server_id, weight in weights.items():
                    carbon_info = carbon_data[server_id]
                    intensity = carbon_info['intensity']
                    region_name = carbon_info['name']
                    flash(f"📊 {region_name}: {intensity:.1f} CO2 → Weight {weight}", "success")
            else:
                flash(f"⚠️ Partially applied carbon weights: {success_count}/{len(weights)} servers updated", "warning")
                for error in failed_servers:
                    flash(f"❌ {error}", "error")
    
    except Exception as e:
        error_msg = f"❌ Error updating carbon weights: {e}"
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'error': error_msg})
        flash(error_msg, "error")
    
    return redirect(url_for('index'))

@app.route('/preset/<preset_name>')
def apply_preset(preset_name):
    """Apply predefined weight presets"""
    presets = {
        'equal': {'n1': 50, 'n2': 50, 'n3': 50, 'name': 'Equal Weights'},
        'west_heavy': {'n1': 100, 'n2': 30, 'n3': 20, 'name': 'West Heavy'},
        'central_heavy': {'n1': 20, 'n2': 100, 'n3': 30, 'name': 'Central Heavy'},
        'east_heavy': {'n1': 20, 'n2': 30, 'n3': 100, 'name': 'East Heavy'},
        'default': {'n1': 1, 'n2': 1, 'n3': 1, 'name': 'Default'}
    }
    
    if preset_name not in presets:
        error_msg = f"Unknown preset: {preset_name}"
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'error': error_msg})
        flash(f"❌ {error_msg}", "error")
        return redirect(url_for('index'))
    
    preset = presets[preset_name].copy()
    preset_display_name = preset.pop('name')
    success_count = 0
    failed_servers = []
    
    # Server name mapping for display
    server_names = {
        'n1': 'US West (California)',
        'n2': 'US Central (Texas)', 
        'n3': 'US East (Mid-Atlantic)'
    }
    
    for server_name, weight in preset.items():
        success, message = api.change_server_weight(server_name, weight)
        if success:
            success_count += 1
        else:
            failed_servers.append(f"{server_name}: {message}")
    
    # Prepare weight updates for display
    weight_updates = []
    for server_id, weight in preset.items():
        weight_updates.append({
            'server': server_id,
            'region': server_names[server_id],
            'weight': weight
        })
    
    if request.headers.get('Accept') == 'application/json':
        # Return JSON response for AJAX requests
        if success_count == len(preset):
            return jsonify({
                'success': True,
                'message': f'Applied "{preset_display_name}" preset successfully',
                'preset_name': preset_display_name,
                'updates': weight_updates,
                'total_updated': success_count
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Partially applied preset: {success_count}/{len(preset)} servers updated',
                'preset_name': preset_display_name,
                'updates': weight_updates,
                'errors': failed_servers,
                'total_updated': success_count
            })
    else:
        # Traditional flash message redirect
        if success_count == len(preset):
            flash(f"✅ Applied '{preset_display_name}' preset successfully", "success")
        else:
            flash(f"⚠️ Partially applied preset: {success_count}/{len(preset)} servers updated", "warning")
            for error in failed_servers:
                flash(f"❌ {error}", "error")
    
    return redirect(url_for('index'))

@app.route('/api/carbon')
def api_carbon():
    """API endpoint to get current carbon intensities"""
    carbon_data = get_carbon_intensities()
    return jsonify({"carbon_data": carbon_data, "timestamp": datetime.now().isoformat()})

@app.route('/haproxy-stats')
def haproxy_stats():
    """Proxy to HAProxy stats dashboard"""
    try:
        response = requests.get(HAPROXY_STATS_URL, timeout=10)
        if response.status_code == 200:
            # Modify the HTML to work through our proxy
            content = response.text.replace('action="', 'action="/haproxy-stats-action?')
            return content, 200, {'Content-Type': 'text/html'}
        else:
            return f"❌ HAProxy Stats not available (Status: {response.status_code})", 503
    except Exception as e:
        return f"❌ Error connecting to HAProxy Stats: {e}", 503

@app.route('/haproxy-stats-action')
def haproxy_stats_action():
    """Handle HAProxy stats actions"""
    try:
        # Forward the request with all query parameters
        url = HAPROXY_STATS_URL
        params = dict(request.args)
        response = requests.get(url, params=params, timeout=10)
        return response.text, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'text/html')}
    except Exception as e:
        return f"❌ Error: {e}", 503

@app.route('/auto-carbon/start')
def start_auto_carbon():
    """Start automatic carbon-based weight updates"""
    if not watttime_api:
        flash("❌ WattTime API not available - cannot start auto-updates", "error")
        return redirect(url_for('index'))
    
    # This would start a background thread for continuous updates
    # For now, just provide manual trigger
    flash("🔄 Auto-carbon updates would run continuously here", "success")
    flash("💡 Currently using manual trigger - click 'Update Carbon Weights' button", "warning")
    return redirect(url_for('index'))

@app.route('/system-status')
def system_status():
    """Show system status and connectivity"""
    status = {
        'haproxy_dataplane': False,
        'haproxy_stats': False,
        'watttime_api': watttime_api is not None,
        'servers_count': 0
    }
    
    # Test HAProxy Dataplane API
    try:
        servers = api.get_servers()
        if servers:
            status['haproxy_dataplane'] = True
            status['servers_count'] = len(servers)
    except:
        pass
    
    # Test HAProxy Stats
    try:
        response = requests.get(HAPROXY_STATS_URL, timeout=5)
        status['haproxy_stats'] = response.status_code == 200
    except:
        pass
    
    return jsonify(status)

# ---------------------------
# Historical Simulation Routes
# ---------------------------

@app.route('/historical-simulation')
def historical_simulation_page():
    """Render historical simulation form and dashboard"""
    return render_template('historical_simulation.html')

@app.route('/historical-simulation/start', methods=['POST'])
def start_historical_simulation():
    """Start the historical simulation based on user inputs"""
    start_date = request.form.get('start_date', 'auto') or 'auto'
    end_date = request.form.get('end_date', 'auto') or 'auto'
    requests_per_hour = int(request.form.get('requests_per_hour', 1000))
    speed_multiplier = float(request.form.get('speed_multiplier', 2.0))

    success = simulation_engine.start_simulation(
        start_date=start_date,
        end_date=end_date,
        requests_per_hour=requests_per_hour,
        speed_multiplier=speed_multiplier
    )

    if success:
        flash('🚀 Historical simulation started!', 'success')
    else:
        flash('❌ Simulation could not be started (maybe already running?)', 'error')

    return redirect(url_for('historical_simulation_page'))

@app.route('/historical-simulation/stop', methods=['POST'])
def stop_historical_simulation():
    """Stop the running historical simulation"""
    simulation_engine.stop_simulation()
    flash('⏹️ Historical simulation stopped.', 'success')
    return redirect(url_for('historical_simulation_page'))

@app.route('/historical-simulation/status')
def historical_simulation_status():
    """Return current simulation status as JSON for front-end polling"""
    return jsonify(simulation_engine.get_simulation_status())

if __name__ == '__main__':
    print("🌱 Green CDN Manager - Starting Up")
    print("=" * 50)
    print(f"📊 Backend: {BACKEND_NAME}")
    print(f"🔗 Dataplane API: {DATAPLANE_HOST}:{DATAPLANE_PORT}")
    print(f"📊 HAProxy Stats: {HAPROXY_STATS_URL}")
    print("=" * 50)
    print("🚀 Access Points:")
    print("  • Weight Manager: http://localhost:5000")
    print("  • Weight Viewer:  http://localhost:5001")
    print("  • HAProxy Stats:  http://localhost:8404/stats")
    print("=" * 50)
    print("🌱 Ready for carbon-aware load balancing!")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 