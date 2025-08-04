from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import math

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_experiment', methods=['POST'])
def run_experiment():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Missing JSON body"), 400

    num_requests = data.get('num_requests')
    experiment_type = data.get('experiment_type')
    num_servers = data.get('num_servers')
    regions = data.get('regions')

    # Now you can use these variables as needed
    # For example, basic validation:
    if num_requests is None or experiment_type is None or num_servers is None or regions is None:
        return jsonify(success=False, message="Missing required fields"), 400

    # Set up servers
    # Array of objects with region, capacity, and carbon intensity
    servers = []
    for region in regions:
        server = {
            'region': region,
            'capacity': 100,  # Example capacity
            'carbon_intensity': 0.5  # Example carbon intensity
        }
        servers.append(server)

    return jsonify(success=True, message="Experiment run successfully")
    

if __name__ == '__main__':
    print("Experiment App - Starting Up")
    print("=" * 30)
    print("Access at: http://localhost:5003")
    print("=" * 30)
    app.run(debug=True, host='0.0.0.0', port=5003)