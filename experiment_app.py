from flask import Flask, render_template_string, request, flash, redirect, url_for
import math

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'

EXPERIMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Experiment - Green CDN</title>
    <script src=\"https://polyfill.io/v3/polyfill.min.js?features=es6\"></script>
    <script src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f2faf2;
            min-height: 100vh;
            color: #1a1a1a;
        }
        body {
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
        .experiment-header {
            max-width: 900px;
            width: 100%;
            margin-bottom: 2.2rem;
            text-align: center;
        }
        .experiment-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #2e7d32;
            margin-bottom: 0.5rem;
            letter-spacing: 0.01em;
        }
        .experiment-desc {
            font-size: 1.18rem;
            color: #333;
            margin-bottom: 0.2rem;
            font-weight: 400;
        }
        .servers-container {
            display: flex;
            justify-content: center;
            gap: 2.5rem;
            flex-wrap: wrap;
            max-width: 1200px;
            margin-bottom: 3rem;
            width: 100%;
        }
        form.experiment-form {
            display: flex;
            width: 100%;
            gap: 2.5rem;
            flex-wrap: wrap;
            justify-content: center;
        }
        .server-box {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 18px;
            padding: 1.5rem 2rem 1.2rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
            width: 340px;
            min-width: 260px;
            display: flex;
            flex-direction: column;
            margin-bottom: 1.5rem;
            margin-right: 0.5rem;
        }
        .experiment-form > .server-box:last-child {
            margin-right: 0;
        }
        .server-name {
            font-weight: 700;
            font-size: 1.25rem;
            color: #2e7d32;
            text-align: center;
            margin-bottom: 1.2rem;
            user-select: none;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .input-group {
            margin-bottom: 1.1rem;
            display: flex;
            align-items: center;
            gap: 0.9rem;
        }
        label {
            font-size: 1rem;
            min-width: 120px;
            color: #2e7d32;
            font-weight: 600;
            user-select: none;
        }
        input[type=\"text\"], input[type=\"number\"] {
            flex-grow: 1;
            padding: 0.38rem 0.7rem;
            border: 1.5px solid #a5d6a7;
            border-radius: 8px;
            font-size: 1.05rem;
            transition: border-color 0.2s ease-in-out;
        }
        input[type=\"text\"]:focus, input[type=\"number\"]:focus {
            outline: none;
            border-color: #388e3c;
            box-shadow: 0 0 6px #81c784;
        }
        button {
            background-color: #4caf50;
            border: none;
            color: white;
            padding: 0.7rem 1.5rem;
            font-weight: 600;
            font-size: 1.15rem;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.25s ease-in-out;
            user-select: none;
        }
        button:hover {
            background-color: #388e3c;
        }
        .total-requests-box {
            background: rgba(255, 255, 255, 0.97);
            border: 1.5px solid #a5d6a7;
            border-radius: 18px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
            width: 600px;
            max-width: 100%;
            display: flex;
            align-items: center;
            gap: 1.2rem;
            margin-top: 2rem;
        }
        .total-requests-box label {
            font-weight: 700;
            font-size: 1.05rem;
            color: #2e7d32;
            min-width: 150px;
            user-select: none;
        }
        .total-requests-box input[type=\"text\"], .total-requests-box input[type=\"number\"] {
            flex-grow: 1;
            padding: 0.5rem 0.8rem;
            border: 1.5px solid #a5d6a7;
            border-radius: 8px;
            font-size: 1.1rem;
        }
        .total-requests-box input[type=\"text\"]:focus, .total-requests-box input[type=\"number\"]:focus {
            outline: none;
            border-color: #388e3c;
            box-shadow: 0 0 8px #81c784;
        }
        .total-requests-box button {
            padding: 0.7rem 1.5rem;
            font-size: 1.15rem;
            user-select: none;
        }
        .results-card {
            background: rgba(255,255,255,0.96);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.13);
            padding: 2.2rem 2.5rem 2.2rem 2.5rem;
            margin-top: 2.5rem;
            width: 100%;
            max-width: 900px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 1.08rem;
            color: #1a1a1a;
        }
        .results-card h2, .results-card h3 {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: #2e7d32;
            font-weight: 700;
            margin-top: 0.5rem;
        }
        .results-card table {
            font-size: 1.08rem;
            width: 100%;
            margin-top: 0.7rem;
            margin-bottom: 1.2rem;
        }
        .results-card th, .results-card td {
            padding: 0.5rem 0.7rem;
            text-align: center;
        }
        .results-card ul, .results-card li {
            font-size: 1.05rem;
        }
        .legend-box {
            background: #f2faf2;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.2rem;
            border: 1px solid #e0e0e0;
            font-size: 1.01rem;
        }
        /* Button Styles Consistent with Main App */
        .btn {
            background: rgba(34, 139, 34, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(34, 139, 34, 0.2);
            color: #2e7d32;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            box-shadow: 0 2px 8px rgba(34, 139, 34, 0.1);
        }
        .btn:hover {
            background: rgba(34, 139, 34, 0.15);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(34, 139, 34, 0.2);
            color: #1b5e20;
            text-decoration: none;
        }
        .btn-green {
            background: rgba(76, 175, 80, 0.1);
            border: 1px solid rgba(76, 175, 80, 0.2);
            color: #2e7d32;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.1);
        }
        .btn-green:hover {
            background: rgba(76, 175, 80, 0.15);
            box-shadow: 0 4px 16px rgba(76, 175, 80, 0.2);
            color: #1b5e20;
        }
        @media (max-width: 900px) {
            .servers-container, form.experiment-form {
                flex-direction: column;
                align-items: center;
            }
            .server-box, .total-requests-box, .results-card {
                width: 95vw;
                min-width: 0;
            }
        }
    </style>
</head>
<body>
    <div class=\"experiment-header\">
        <div class=\"experiment-title\">Green CDN Load Balancing Experiment</div>
        <div class=\"experiment-desc\">
            Compare the environmental and operational impact of two load balancing strategies: <b>Round Robin</b> (baseline) and <b>Carbon-Aware</b>.<br>
            Enter the characteristics for each server and the total number of requests, then run the experiment to see the difference in total carbon emissions, cost, and latency.
        </div>
    </div>
    <div class=\"servers-container\">
        <form method=\"POST\" action=\"/run_experiment\" class=\"experiment-form\">
        {% for server in servers %}
        <div class=\"server-box\">
            <div class=\"server-name\">{{ server.upper() }}</div>
            <div class=\"input-group\">
                <label for=\"{{ server }}-capacity\">Capacity</label>
                <input type=\"number\" id=\"{{ server }}-capacity\" name=\"{{ server }}-capacity\" placeholder=\"Enter capacity\" min=\"0\" required />
            </div>
            <div class=\"input-group\">
                <label for=\"{{ server }}-carbon\">Carbon Intensity</label>
                <input type=\"number\" step=\"any\" id=\"{{ server }}-carbon\" name=\"{{ server }}-carbon\" placeholder=\"gCO₂/kWh\" min=\"0\" required />
            </div>
            <div class=\"input-group\">
                <label for=\"{{ server }}-cost\">Cost/Request</label>
                <input type=\"number\" step=\"any\" id=\"{{ server }}-cost\" name=\"{{ server }}-cost\" placeholder=\"$ per request\" min=\"0\" required />
            </div>
            <div class=\"input-group\">
                <label for=\"{{ server }}-latency\">Latency</label>
                <input type=\"number\" step=\"any\" id=\"{{ server }}-latency\" name=\"{{ server }}-latency\" placeholder=\"ms\" min=\"0\" required />
            </div>
        </div>
        {% endfor %}
        <div style=\"flex-basis: 100%; height: 0;\"></div>
        <div class=\"total-requests-box\">
            <label for=\"total-requests\">Total Requests</label>
            <input type=\"number\" id=\"total-requests\" name=\"total-requests\" placeholder=\"Enter total number of requests\" min=\"1\" required />
            <button type=\"submit\" class=\"btn btn-green\">Run Experiment</button>
        </div>
        </form>
    </div>
    {% if results %}
    <div class=\"results-card\" id=\"results-mathjax\">
        {{ results|safe }}
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET'])
def experiment():
    servers = ['server1', 'server2', 'server3']
    return render_template_string(EXPERIMENT_TEMPLATE, servers=servers, results=None)

@app.route('/run_experiment', methods=['POST'])
def run_experiment():
    servers = ['server1', 'server2', 'server3']
    try:
        # Gather input values
        server_data = []
        for s in servers:
            capacity = float(request.form.get(f'{s}-capacity', 0))
            carbon = float(request.form.get(f'{s}-carbon', 0))
            cost = float(request.form.get(f'{s}-cost', 0))
            latency = float(request.form.get(f'{s}-latency', 0))
            server_data.append({'name': s, 'capacity': capacity, 'carbon': carbon, 'cost': cost, 'latency': latency})
        total_requests = int(request.form.get('total-requests', 0))
        # --- Round Robin Policy ---
        rr_requests = [total_requests // 3 for _ in range(3)]
        for i in range(total_requests % 3):
            rr_requests[i] += 1
        rr_carbon = sum(rr_requests[i] * server_data[i]['carbon'] for i in range(3))
        rr_cost = sum(rr_requests[i] * server_data[i]['cost'] for i in range(3))
        rr_latency = sum(rr_requests[i] * server_data[i]['latency'] for i in range(3)) / total_requests if total_requests else 0
        # --- Carbon-Aware Policy ---
        inv_carbons = [1.0 / (server_data[i]['carbon'] if server_data[i]['carbon'] > 0 else 1e-6) for i in range(3)]
        total_inv = sum(inv_carbons)
        ca_weights = [x / total_inv for x in inv_carbons]
        ca_requests = [int(round(total_requests * w)) for w in ca_weights]
        # Adjust for rounding errors
        diff = total_requests - sum(ca_requests)
        for i in range(abs(diff)):
            ca_requests[i % 3] += 1 if diff > 0 else -1
        ca_carbon = sum(ca_requests[i] * server_data[i]['carbon'] for i in range(3))
        ca_cost = sum(ca_requests[i] * server_data[i]['cost'] for i in range(3))
        ca_latency = sum(ca_requests[i] * server_data[i]['latency'] for i in range(3)) / total_requests if total_requests else 0
        # --- Savings ---
        carbon_savings = rr_carbon - ca_carbon
        cost_savings = rr_cost - ca_cost
        latency_savings = rr_latency - ca_latency
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
        <li>Total Cost: $$\text{Cost} = \sum_{i=1}^S r_i \times \text{cost}_i$$</li>
        <li>Avg Latency: $$L = \frac{1}{N} \sum_{i=1}^S r_i \times l_i$$</li>
        <li>Savings: $$\text{Savings} = \text{Baseline} - \text{Carbon-Aware}$$</li>
        </ul>
        '''
        legend_html = '''
        <div class="legend-box">
        <b>Legend:</b>
        <ul>
        <li><b>N</b>: Total number of requests</li>
        <li><b>S</b>: Number of servers (3)</li>
        <li><b>r<sub>i</sub></b>: Requests sent to server <i>i</i></li>
        <li><b>c<sub>i</sub></b>: Carbon intensity of server <i>i</i> (gCO₂/kWh)</li>
        <li><b>w<sub>i</sub></b>: Weight for server <i>i</i> (carbon-aware)</li>
        <li><b>cost<sub>i</sub></b>: Cost per request for server <i>i</i></li>
        <li><b>l<sub>i</sub></b>: Latency for server <i>i</i> (ms)</li>
        </ul>
        </div>
        '''
        results_html = f"""
        <h2>Experiment Results</h2>
        {legend_html}
        <h3>Inputs</h3>
        <ul>
        {''.join([f'<li>{d["name"]}: Capacity={d["capacity"]}, Carbon={d["carbon"]}, Cost={d["cost"]}, Latency={d["latency"]}</li>' for d in server_data])}
        <li>Total Requests: {total_requests}</li>
        </ul>
        {latex_formulas}
        <h3>Results</h3>
        <table border=1 cellpadding=6 style='border-collapse:collapse;'>
        <tr><th>Policy</th><th>Requests</th><th>Total Carbon</th><th>Total Cost</th><th>Avg Latency</th></tr>
        <tr><td>Round Robin</td><td>{fmtarr(rr_requests)}</td><td>{rr_carbon:.2f}</td><td>{rr_cost:.2f}</td><td>{rr_latency:.2f} ms</td></tr>
        <tr><td>Carbon-Aware</td><td>{fmtarr(ca_requests)}</td><td>{ca_carbon:.2f}</td><td>{ca_cost:.2f}</td><td>{ca_latency:.2f} ms</td></tr>
        </table>
        <h3>Savings (Round Robin - Carbon-Aware)</h3>
        <ul>
        <li>Carbon Savings: {carbon_savings:.2f}</li>
        <li>Cost Savings: {cost_savings:.2f}</li>
        <li>Latency Savings: {latency_savings:.2f} ms</li>
        </ul>
        """
        return render_template_string(EXPERIMENT_TEMPLATE, servers=servers, results=results_html)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('experiment'))

if __name__ == '__main__':
    print("Experiment App - Starting Up")
    print("=" * 30)
    print("Access at: http://localhost:5002")
    print("Shows three servers with capacity/data inputs and total requests input")
    print("=" * 30)
    app.run(debug=True, host='0.0.0.0', port=5002)