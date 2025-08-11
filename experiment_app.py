from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import requests
from requests.auth import HTTPBasicAuth
import math
import csv
from dateutil import parser

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'

BASE_URL = "http://haproxy:5555/v2"
AUTH = HTTPBasicAuth('admin', 'password')
BACKEND_NAME = "local_servers"

@app.route('/')
def index():
    return render_template('experiment.html')

@app.route('/run_experiment', methods=['POST'])
def run_experiment():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Missing JSON body"), 400

    num_requests = int(data.get('num_requests'))
    experiment_type = data.get('experiment_type')
    num_servers = int(data.get('num_servers'))
    servers = data.get('servers')  # Expecting list of dicts with region and capacity

    #Basic validation:
    if num_requests is None or experiment_type is None or num_servers is None or servers is None:
        return jsonify(success=False, message="Missing required fields"), 400

    print("servers are: ", servers)

    # Ensure there are {num_servers} number of servers
    # Get old servers
    old_servers = get_servers()
    print("old servers are: ", old_servers)

    # Delete old servers
    for server in old_servers:
        print("Deleting server:", server["name"])
        if not delete_server(server["name"]):
            return jsonify(success=False, message=f"Failed to delete server {server['name']}"), 500

    # Create {num_servers} new servers
    for i in range(num_servers):
        server_name = f"s{i + 1}"
        server_address = f"web{i + 1}"
        print("Adding server:", server_name)
        if not add_server(server_name, server_address, weight=1):
            return jsonify(success=False, message=f"Failed to create server {server_name}"), 500
        

    results = []
    weights = [1 for _ in range(num_servers)]
    intensities = []
    time = 0

    # # Process all requests
    # for i in range(num_requests):
    #     # Update weights if needed on every 10th request
    #     if experiment_type == 'carbon_aware' and i % 10 == 0:
    #         intensities = [read_carbon_intensity(server.get('region'), f'2020-01-01 {(time % 24):02}:00:00+00:00') for server in servers]
    #         weights = [1 / intensity if intensity > 0 else 0 for intensity in intensities]
    #         update
    #     # Run a request
    #     response = requests.get("http://haproxy:80")
    #     # See which server handled it and aggregate results



    # Set up servers (array of objects with region, capacity, and starting carbon intensity)
    server_starter_data = []
    for server in servers:
        # Read first carbon intensity from CSV file
        carbon_intensity = read_carbon_intensity(server.get('region'), '2020-01-01 00:00:00+00:00') # Reads the first intensity
        if carbon_intensity is None:
            return jsonify(success=False, message=f"Could not read first carbon intensity for region {server.get('region')}"), 400

        server = {
            'region': server.get('region'),
            'capacity': server.get('capacity', 100),  # Default capacity
            'carbon_intensity': carbon_intensity
        }
        server_starter_data.append(server)   

    return jsonify(success=True, message="Experiment ran successfully", data=server_starter_data)

def get_servers():
    """Get current server configurations"""
    try:
        url = f"{BASE_URL}/services/haproxy/configuration/servers"
        params = {"backend": BACKEND_NAME}
        response = requests.get(url, auth=AUTH, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        return None
    except Exception as e:
        print(f"Error getting servers: {e}")
        return None
    
def delete_server(server_name):
    """Delete a server by name"""
    try:
        url = f"{BASE_URL}/services/haproxy/configuration/servers/{server_name}"
        params = {"backend": BACKEND_NAME, "version": get_version()}
        response = requests.delete(url, auth=AUTH, params=params, timeout=10)

        print(server_name, "delete server status:", response.status_code)
        if response.status_code == 202 or response.status_code == 204:
            return True
        return False
    except Exception as e:
        print(f"Error deleting server {server_name}: {e}")
        return False
    
def add_server(server_name, server_address, weight=1):
    """Add a server by name"""
    try:
        url = f"{BASE_URL}/services/haproxy/configuration/servers"
        params = {"backend": BACKEND_NAME, "version": get_version()}
        data = {
            "name": server_name,
            "weight": weight,
            "address": server_address,
            "check": "enabled",
            "port": 80
        }
        response = requests.post(url, auth=AUTH, params=params, json=data, timeout=10)
        print(server_name, "add server status:", response.status_code)

        if response.status_code == 201 or response.status_code == 202:
            return True
        return False
    except Exception as e:
        print(f"Error adding server {server_name}: {e}")
        return False

@app.route('/run_calculator', methods=['POST'])
def run_calculator():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Missing JSON body"), 400

    total_requests = int(data.get('num_requests'))
    experiment_type = data.get('experiment_type')
    num_servers = int(data.get('num_servers'))
    servers = data.get('servers')  # Expecting list of dicts with region and capacity

    #Basic validation:
    if total_requests is None or experiment_type is None or num_servers is None or servers is None:
        return jsonify(success=False, message="Missing required fields"), 400

    # Set up servers
    # Array of objects with region, capacity, and starting carbon intensity
    server_starter_data = []
    for server in servers:
        # Read first carbon intensity from CSV file or use 1 for baseline
        carbon_intensity = None # Default if not found
        if experiment_type == 'carbon_aware':
            carbon_intensity = read_carbon_intensity(server.get('region'), '2020-01-01 00:00:00+00:00') # Reads the first intensity
        else:
            carbon_intensity = 1.0
        if carbon_intensity is None:
            return jsonify(success=False, message=f"Could not read first carbon intensity for region {server.get('region')}"), 400

        server = {
            'region': server.get('region'),
            'capacity': server.get('capacity', 100),  # Default capacity
            'carbon_intensity': carbon_intensity
        }
        server_starter_data.append(server)
    
    servers = []
    try:
        # --- Round Robin Policy ---
        rr_requests = [total_requests // num_servers for _ in range(num_servers)]
        for i in range(total_requests % num_servers):
            rr_requests[i] += 1
        rr_carbon = sum(rr_requests[i] * server_starter_data[i]['carbon_intensity'] for i in range(num_servers))
        # --- Carbon-Aware Policy ---
        inv_carbons = [1.0 / (server_starter_data[i]['carbon_intensity'] if server_starter_data[i]['carbon_intensity'] > 0 else 1e-6) for i in range(num_servers)]
        total_inv = sum(inv_carbons)
        ca_weights = [x / total_inv for x in inv_carbons]
        ca_requests = [int(round(total_requests * w)) for w in ca_weights]
        # Adjust for rounding errors
        diff = total_requests - sum(ca_requests)
        for i in range(abs(diff)):
            ca_requests[i % num_servers] += 1 if diff > 0 else -1
        ca_carbon = sum(ca_requests[i] * server_starter_data[i]['carbon_intensity'] for i in range(num_servers))
        # --- Savings ---
        carbon_savings = rr_carbon - ca_carbon
        
        # --- Show formulas and results ---
        def fmtarr(arr):
            return ', '.join(str(x) for x in arr)
        # LaTeX formulas for MathJax
        latex_formulas = r'''
        <h3>Formulas</h3>
        <ul>
        <li>Round Robin Requests: $$r_i = \left\lfloor \frac{N}{S} \right\rfloor$$ (plus distribute remainder)</li>
        <li>Carbon-Aware Weights: $$w_i = \frac{1/c_i}{\sum_{j=1}^S 1/c_j}$$</li>
        <li>Requests per server (CA): $$r_i = N \times w_i$$</li>
        <li>Total Carbon: $$C = \sum_{i=1}^S r_i \times c_i$$</li>
        <li>Savings: $$\text{Savings} = \text{Baseline} - \text{Carbon-Aware}$$</li>
        </ul>
        '''
        legend_html = '''
        <div class="legend-box">
        <b>Legend:</b>
        <ul>
        <li><b>N</b>: Total number of requests</li>
        <li><b>S</b>: Number of servers ({num_servers})</li>
        <li><b>r<sub>i</sub></b>: Requests sent to server <i>i</i></li>
        <li><b>c<sub>i</sub></b>: Carbon intensity of server <i>i</i> (gCO₂/kWh)</li>
        <li><b>w<sub>i</sub></b>: Weight for server <i>i</i> (carbon-aware)</li>
        </ul>
        </div>
        '''
        results_html = f"""
        <h2>Experiment Results</h2>
        {legend_html}
        <h3>Inputs</h3>
        <ul>
        {''.join([f'<li>{d["region"]}: Capacity={d["capacity"]}, Carbon={d["carbon_intensity"]}</li>' for d in server_starter_data])}
        <li>Total Requests: {total_requests}</li>
        </ul>
        {latex_formulas}
        <h3>Results</h3>
        <table border=1 cellpadding=6 style='border-collapse:collapse;'>
        <tr><th>Policy</th><th>Requests</th><th>Total Carbon</th></tr>
        <tr><td>Round Robin</td><td>{fmtarr(rr_requests)}</td><td>{rr_carbon:.2f}</td></tr>
        <tr><td>Carbon-Aware</td><td>{fmtarr(ca_requests)}</td><td>{ca_carbon:.2f}</td></tr>
        </table>
        <h3>Savings (Round Robin - Carbon-Aware)</h3>
        <ul>
        <li>Carbon Savings: {carbon_savings:.2f}</li>
        </ul>
        """
        print("Experiment completed successfully.")
        return jsonify(success=True, message="Experiment completed successfully", results=results_html), 200
    except Exception as e:
        return jsonify(success=False, message=f"Error with calculations: {e}"), 400


def read_carbon_intensity(region, time_str):
    """
    Reads the carbon intensity for a given region at a specified time.
    
    :param region: str, used to find the CSV file (e.g., 'US-CAL-BANC')
    :param time_str: str, datetime string, e.g., '2020-01-01 05:00:00+00:00'
    :return: float carbon intensity, or None if not found
    """
    filename = f"/app/data/marginal_emissions_{region.upper()}.csv"
    
    target_time = parser.parse(time_str)

    try:
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row_time = parser.parse(row['datetime'])
                if row_time == target_time:
                    return float(row['marginal_carbon_intensity_avg'])
        # If no exact match found:
        return None
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return None
    
def get_version():
        """Get current configuration version"""
        try:
            url = f"{BASE_URL}/services/haproxy/configuration/version"
            response = requests.get(url, auth=AUTH, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting version: {e}")
            return None

if __name__ == '__main__':
    print("Experiment App - Starting Up")
    print("=" * 30)
    print("Access at: http://localhost:5003")
    print("=" * 30)
    app.run(debug=True, host='0.0.0.0', port=5003)