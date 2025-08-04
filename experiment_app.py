from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import math
import csv
from dateutil import parser

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'

@app.route('/')
def index():
    return render_template('experiment.html')

@app.route('/run_experiment', methods=['POST'])
def run_experiment():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Missing JSON body"), 400

    num_requests = data.get('num_requests')
    experiment_type = data.get('experiment_type')
    num_servers = data.get('num_servers')
    servers = data.get('servers')  # Expecting list of dicts with region and capacity

    #Basic validation:
    if num_requests is None or experiment_type is None or num_servers is None or servers is None:
        return jsonify(success=False, message="Missing required fields"), 400

    # Set up servers
    # Array of objects with region, capacity, and carbon intensity
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

    return jsonify(success=True, message="Experiment run successfully", data=server_starter_data)

def read_carbon_intensity(region, time_str):
    """
    Reads the carbon intensity for a given region at a specified time.
    
    :param region: str, used to find the CSV file (e.g., 'us-cal-banc')
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

if __name__ == '__main__':
    print("Experiment App - Starting Up")
    print("=" * 30)
    print("Access at: http://localhost:5003")
    print("=" * 30)
    app.run(debug=True, host='0.0.0.0', port=5003)