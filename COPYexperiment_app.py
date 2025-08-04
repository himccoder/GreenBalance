from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
import requests

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'

EXPERIMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Experiment - Green CDN</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f2faf2;
            min-height: 100vh;
            color: #1a1a1a;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem 1rem;
            overflow-x: hidden;
            position: relative;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background:
                radial-gradient(circle at 20% 80%, rgba(34, 139, 34, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(76, 175, 80, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.8) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        .servers-container {
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            flex-wrap: wrap;
            max-width: 920px;
            margin-bottom: 3rem;
            width: 100%;
        }
        .server-box {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(34, 139, 34, 0.2);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            width: 280px;
            display: flex;
            flex-direction: column;
        }
        .server-name {
            font-weight: 700;
            font-size: 1.25rem;
            color: #2e7d32;
            text-align: center;
            margin-bottom: 1rem;
            user-select: none;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .input-group {
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: nowrap; /* Prevent wrapping so inputs/buttons stay on one line */
        }

        .input-group label {
            flex-shrink: 0;
            width: 70px; /* fixed width to align labels */
            white-space: nowrap;
        }

        .input-group input[type="text"] {
            flex: 1 1 auto; /* expand to fill remaining space */
            min-width: 0; /* allow shrinking properly in flex container */
        }

        .input-group button {
            flex-shrink: 0; /* prevent button from shrinking */
            white-space: nowrap;
        }
        label {
            font-size: 0.9rem;
            min-width: 70px;
            color: #2e7d32;
            font-weight: 600;
            user-select: none;
        }
        input[type="text"], input[type="number"] {
            flex-grow: 1;
            padding: 0.35rem 0.6rem;
            border: 1.5px solid #a5d6a7;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s ease-in-out;
        }
        input[type="text"]:focus, input[type="number"]:focus {
            outline: none;
            border-color: #388e3c;
            box-shadow: 0 0 6px #81c784;
        }
        button, .button {
            background-color: #4caf50;
            border: none;
            color: white;
            padding: 0.45rem 0.9rem;
            font-weight: 600;
            font-size: 0.95rem;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.25s ease-in-out;
            user-select: none;
        }
        button:hover, .button:hover {
            background-color: #388e3c;
        }
        .total-requests-box {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(34, 139, 34, 0.2);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            width: 600px;
            max-width: 100%;
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .total-requests-box label {
            font-weight: 700;
            font-size: 1rem;
            color: #2e7d32;
            min-width: 150px;
            user-select: none;
        }
        .total-requests-box input[type="text"] {
            flex-grow: 1;
            padding: 0.5rem 0.8rem;
            border: 1.5px solid #a5d6a7;
            border-radius: 8px;
            font-size: 1.1rem;
        }
        .total-requests-box input[type="text"]:focus {
            outline: none;
            border-color: #388e3c;
            box-shadow: 0 0 8px #81c784;
        }
        .select-experiment-box {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(34, 139, 34, 0.2);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            width: 600px;
            max-width: 100%;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            align-items: center;
            user-select: none;
        }
        .select-experiment-box label {
            font-weight: 700;
            font-size: 1.2rem;
            color: #2e7d32;
        }
        .experiment-buttons {
            display: flex;
            gap: 2rem;
            margin-top: 0.5rem;
        }
        .experiment-buttons button {
            padding: 0.7rem 1.8rem;
            font-weight: 700;
            font-size: 1.1rem;
            cursor: pointer;
            user-select: none;
        }
    </style>
</head>
<body>
    <div class="servers-container">
        {% for server in servers %}
        <div class="server-box">
            <div class="server-name">{{ server.upper() }}</div>
            <div class="input-group">
                <label for="{{ server }}-capacity">Capacity</label>
                <input type="text" id="{{ server }}-capacity" name="{{ server }}-capacity" />
            </div>
            <div class="input-group">
                <label for="{{ server }}-data">Data</label>
                <input type="text" id="{{ server }}-data" name="{{ server }}-data" />
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="total-requests-box">
        <label for="total-requests">Total Requests</label>
        <input type="number" id="total-requests" name="total-requests" placeholder="Enter total number of requests" />
    </div>

    <div class="select-experiment-box">
        <label>Select Experiment</label>
        <div class="experiment-buttons">
            <input type="button" id="baseline" class="button" value="Baseline" />
            <input type="button" id="carbon" class="button" value="Carbon Aware" />
        </div>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        <ul style="max-width:600px; margin:1rem auto; padding:0; list-style:none;">
        {% for category, message in messages %}
            <li style="color: {% if category == 'error' %}red{% elif category == 'success' %}green{% else %}black{% endif %}; padding: 0.25rem 0; font-weight:600;">{{ message }}</li>
        {% endfor %}
        </ul>
    {% endif %}
    {% endwith %}
    <script>
        function gatherData() {
            const servers = {{ servers|tojson }};
            const result = {
                servers: {},
                total_requests: null
            };

            // Gather server capacities and data
            for (const server of servers) {
                const capacityInput = document.getElementById(`${server}-capacity`);
                const dataInput = document.getElementById(`${server}-data`);

                if (!capacityInput || !dataInput) {
                    return null; // Missing inputs (should not happen)
                }

                const capacity = capacityInput.value.trim();
                const data = dataInput.value.trim();

                result.servers[server] = {
                    capacity,
                    data
                };
            }

            // Gather total requests
            const totalRequestsInput = document.getElementById("total-requests");
            if (!totalRequestsInput) {
                return null;
            }
            result.total_requests = totalRequestsInput.value.trim();

            return result;
        }

        document.addEventListener('DOMContentLoaded', function() {
            const baselineButton = document.getElementById("baseline");
            if (baselineButton) {
                baselineButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    const data = gatherData();

                    // Validate data - check none of these fields are missing or empty
                    if (!data) {
                        alert("Internal error: Could not get server inputs.");
                        return;
                    }

                    for (const [server, vals] of Object.entries(data.servers)) {
                        if (!vals.capacity) {
                            alert(`Please enter capacity for ${server.toUpperCase()}.`);
                            return;
                        }
                        if (!vals.data) {
                            alert(`Please enter data for ${server.toUpperCase()}.`);
                            return;
                        }
                    }

                    if (!data.total_requests) {
                        alert("Please enter total number of requests.");
                        return;
                    }

                    console.log("data validated");
                    console.log("running baseline");

                    // Send POST request to /run_baseline with JSON data
                    fetch("/run_baseline", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        },
                        body: JSON.stringify(data)
                    })
                    .then(response => response.json())
                    .then(respData => {
                        if(respData.success) {
                            alert("Baseline experiment run successfully!");
                            // Optionally refresh or update UI here
                        } else {
                            alert("Failed to run baseline experiment: " + (respData.message || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        alert("Error communicating with server: " + error);
                    });
                });
            }
            const carbonButton = document.getElementById("carbon");
            if (carbonButton) {
                carbonButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    const data = gatherData();

                    // Validate data - check none of these fields are missing or empty
                    if (!data) {
                        alert("Internal error: Could not get server inputs.");
                        return;
                    }

                    for (const [server, vals] of Object.entries(data.servers)) {
                        if (!vals.capacity) {
                            alert(`Please enter capacity for ${server.toUpperCase()}.`);
                            return;
                        }
                        if (!vals.data) {
                            alert(`Please enter data for ${server.toUpperCase()}.`);
                            return;
                        }
                    }

                    if (!data.total_requests) {
                        alert("Please enter total number of requests.");
                        return;
                    }

                    console.log("data validated");
                    console.log("running carbon aware");

                    // Send POST request to /run_carbon_aware with JSON data
                    fetch("/run_carbon_aware", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        },
                        body: JSON.stringify(data)
                    })
                    .then(response => response.json())
                    .then(respData => {
                        if(respData.success) {
                            alert("Baseline experiment run successfully!");
                            // Optionally refresh or update UI here
                        } else {
                            alert("Failed to run baseline experiment: " + (respData.message || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        alert("Error communicating with server: " + error);
                    });
                });
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def experiment():
    servers = ['server1', 'server2', 'server3']
    return render_template_string(EXPERIMENT_TEMPLATE, servers=servers)

@app.route('/run_experiment', methods=['POST'])
def run_experiment():
    experiment = request.form.get('experiment')
    if experiment == 'baseline':
        try:
            resp = requests.get("http://weight-manager:5000/preset/default", timeout=5)
            if resp.status_code == 200:
                flash("✅ Applied baseline preset successfully!", "success")
            else:
                flash(f"❌ Failed to apply preset: {resp.status_code} {resp.text}", "error")
        except Exception as e:
            flash(f"❌ Error applying baseline preset: {e}", "error")
    elif experiment == 'carbon_aware':
        flash("ℹ️ Carbon aware experiment does nothing currently.", "info")
    else:
        flash("⚠️ Unknown experiment option.", "error")
    return redirect(url_for('experiment'))

@app.route('/run_baseline', methods=["POST"])
def run_baseline_experiment():
    data = request.get_json()
    try:
        resp = requests.get("http://weight-manager:5000/preset/default", timeout=5)
        if resp.status_code == 200:
            flash("✅ Applied baseline preset successfully!", "success")
            # Run baseline experiment
            if not data:
                return jsonify(success=False, message="No JSON payload received"), 400

            servers = data.get("servers")
            total_requests = data.get("total_requests")

            # Basic validation
            if not servers or not isinstance(servers, dict):
                return jsonify(success=False, message="Missing or invalid 'servers' data"), 400
            if not total_requests:
                return jsonify(success=False, message="Missing 'total_requests'"), 400

            # Example: iterate over servers and log or process capacity and data
            for server_name, details in servers.items():
                capacity = details.get("capacity")
                # You can convert capacity to int, float, etc. as needed:
                try:
                    capacity_val = int(capacity)
                except (ValueError, TypeError):
                    return jsonify(success=False, message=f"Invalid capacity for {server_name}"), 400
                
                details.set("data", deconstruct_data(details.get("data"))) # Convert from string to list
                info = details.get("data")
                
                # Process data and capacity as needed here
                print(f"Server: {server_name}, Capacity: {capacity_val}, Data: {info}")

            # Also process total_requests as needed
            try:
                total_requests_val = int(total_requests)
            except (ValueError, TypeError):
                return jsonify(success=False, message="Invalid total_requests value"), 400

            print(f"Total Requests: {total_requests_val}")

            # Perform your baseline experiment logic here ...
            for i in range(total_requests):
                # Simulate request
                response = requests.get("http://haproxy:80", timeout=5)
                if response.status_code == 200:
                    json = response.json()
                    server = json
                # See which server handles it
                # Keep track of data

            # Return success response (can include additional info if you want)
            return jsonify(success=True, message="Baseline experiment processed successfully")

        else:
            flash(f"❌ Failed to apply preset: {resp.status_code} {resp.text}", "error")
            return jsonify(success=False, message=resp.text)

    except Exception as e:
        flash(f"❌ Error applying baseline preset: {e}", "error")
        return jsonify(success=False, message=e)

@app.route('/run_carbon_aware', methods=["POST"])
def run_carbon_aware_experiment():
    pass

def deconstruct_data(server_data):
    # Split the string by commas, strip whitespace, and convert each piece to int
    return [int(x.strip()) for x in server_data.split(',') if x.strip()]

if __name__ == '__main__':
    print("Experiment App - Starting Up")
    print("=" * 30)
    print("Access at: http://localhost:5002")
    print("Shows servers with capacity inputs and experiment selection")
    print("=" * 30)
    app.run(debug=True, host='0.0.0.0', port=5002)