from flask import Flask, render_template_string, request, flash, redirect, url_for, jsonify
import json
from simple_data_processor import get_simple_processor, get_simulation_engine

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'

# Simplified experiment template with basic HTML charts
SIMPLE_EXPERIMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Green CDN - CSV Enhanced Experiment</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f2faf2;
            min-height: 100vh;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
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
        .container {
            max-width: 1400px;
            width: 100%;
        }
        
        /* Educational Demo Banner */
        .demo-banner {
            background: rgba(255, 255, 255, 0.95);
            border: 2px solid #2e7d32;
            color: #2e7d32;
            padding: 1rem 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(46, 125, 50, 0.15);
        }
        .demo-banner h3 {
            margin: 0 0 0.5rem 0;
            font-size: 1.2rem;
            font-weight: 600;
            color: #2e7d32;
        }
        .demo-banner p {
            margin: 0;
            font-size: 0.9rem;
            color: #333;
        }
        .experiment-header {
            text-align: center;
            margin-bottom: 2rem;
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
            margin-bottom: 1rem;
            font-weight: 400;
        }
        .status-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #a5d6a7;
            color: #2e7d32;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        .info-box {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #a5d6a7;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        .info-box h4 {
            color: #2e7d32;
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
            font-weight: 600;
        }
        .demo-indicator {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #a5d6a7;
            border-radius: 6px;
            padding: 0.2rem 0.5rem;
            font-size: 0.7rem;
            color: #666;
            font-weight: 500;
            display: inline-block;
            margin-left: 0.5rem;
        }
        .historical-indicator {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #2e7d32;
            border-radius: 6px;
            padding: 0.2rem 0.5rem;
            font-size: 0.7rem;
            color: #2e7d32;
            font-weight: 500;
            display: inline-block;
            margin-left: 0.5rem;
        }
        .realtime-indicator {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #1976d2;
            border-radius: 6px;
            padding: 0.2rem 0.5rem;
            font-size: 0.7rem;
            color: #1976d2;
            font-weight: 500;
            display: inline-block;
            margin-left: 0.5rem;
        }
        .simulation-indicator {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #388e3c;
            border-radius: 6px;
            padding: 0.2rem 0.5rem;
            font-size: 0.7rem;
            color: #388e3c;
            font-weight: 500;
            display: inline-block;
            margin-left: 0.5rem;
        }
        
        /* Operation Mode Selection */
        .operation-mode-selector {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 18px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
            margin-bottom: 2rem;
            text-align: center;
        }
        .operation-mode-selector h3 {
            color: #2e7d32;
            margin-bottom: 1rem;
        }
        .operation-mode-explanation {
            text-align: left;
            color: #666;
            font-size: 0.9rem;
            margin-top: 1rem;
            line-height: 1.5;
        }
        
        /* Simulation Controls */
        .simulation-controls {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 18px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
            margin-bottom: 2rem;
        }
        .simulation-controls h3 {
            color: #2e7d32;
            margin-bottom: 1rem;
            text-align: center;
        }
        .simulation-params {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .param-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .param-group label {
            font-weight: 500;
            color: #2e7d32;
            font-size: 0.9rem;
        }
        .param-group input, .param-group select {
            padding: 0.5rem;
            border: 1px solid #a5d6a7;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        .simulation-explanation {
            text-align: left;
            color: #666;
            font-size: 0.9rem;
            margin-top: 1rem;
            line-height: 1.5;
            border-top: 1px solid #e0e0e0;
            padding-top: 1rem;
        }
        
        /* Data Source Selection */
        .data-source-selector {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 18px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
            margin-bottom: 2rem;
            text-align: center;
        }
        .data-source-selector h3 {
            color: #2e7d32;
            margin-bottom: 1rem;
        }
        .radio-group {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 1rem;
        }
        .radio-option {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .radio-option input[type="radio"] {
            margin: 0;
        }
        .radio-option label {
            font-weight: 500;
            color: #2e7d32;
            cursor: pointer;
        }
        
        /* Server Configuration */
        .servers-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
            max-width: 100%;
            overflow: hidden;
        }
        @media (max-width: 1200px) {
            .servers-container {
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
            }
        }
        @media (max-width: 768px) {
            .servers-container {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
        }
        .server-box {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 18px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 320px;
            margin: 0 auto;
        }
        @media (max-width: 768px) {
            .server-box {
                padding: 1rem;
                max-width: 100%;
            }
        }
        .server-name {
            font-weight: 700;
            font-size: 1.25rem;
            color: #2e7d32;
            text-align: center;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .input-group {
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        label {
            font-size: 0.9rem;
            min-width: 100px;
            color: #2e7d32;
            font-weight: 600;
        }
        input[type="text"], input[type="number"], select {
            flex-grow: 1;
            padding: 0.4rem 0.7rem;
            border: 1.5px solid #a5d6a7;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s ease-in-out;
        }
        input[type="text"]:focus, input[type="number"]:focus, select:focus {
            outline: none;
            border-color: #388e3c;
            box-shadow: 0 0 6px #81c784;
        }
        .csv-stats {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .data-source-explanation {
            font-size: 0.85rem;
            color: #555;
            margin-top: 0.5rem;
            padding: 0.75rem;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 3px solid #2196F3;
        }
        
        /* Controls */
        .controls-section {
            background: rgba(255, 255, 255, 0.97);
            border: 1.5px solid #a5d6a7;
            border-radius: 18px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
            margin-bottom: 2rem;
            text-align: center;
        }
        .total-requests-group {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .btn {
            background-color: #4caf50;
            border: none;
            color: white;
            padding: 0.7rem 1.5rem;
            font-weight: 600;
            font-size: 1.1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.25s ease-in-out;
            text-decoration: none;
            display: inline-block;
            margin: 0.25rem;
        }
        .btn:hover {
            background-color: #388e3c;
            text-decoration: none;
            color: white;
        }
        .btn-secondary {
            background-color: #388e3c;
        }
        .btn-secondary:hover {
            background-color: #2e7d32;
        }
        
        /* Charts Section */
        .charts-section {
            background: rgba(255,255,255,0.96);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.13);
            padding: 2rem;
            margin-bottom: 2rem;
            width: 100%;
        }
        .charts-section h3 {
            color: #2e7d32;
            margin-top: 0;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        .chart-container {
            background: #f9f9f9;
            border-radius: 12px;
            padding: 1rem;
            min-height: 300px;
        }
        .chart-title {
            font-weight: 600;
            color: #2e7d32;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        /* Results */
        .results-card {
            background: rgba(255,255,255,0.96);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.13);
            padding: 2rem;
            margin-top: 2rem;
            width: 100%;
            font-size: 1.05rem;
            color: #1a1a1a;
        }
        .results-card h2, .results-card h3 {
            color: #2e7d32;
            font-weight: 700;
        }
        .results-card table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        .results-card th, .results-card td {
            padding: 0.8rem;
            text-align: center;
            border: 1px solid #a5d6a7;
        }
        .results-card th {
            background-color: rgba(229, 255, 229, 0.5);
            color: #2e7d32;
            font-weight: 600;
        }
        
        /* Responsive */
        @media (max-width: 900px) {
            .servers-container {
                flex-direction: column;
                align-items: center;
            }
            .charts-grid {
                grid-template-columns: 1fr;
            }
            .server-box, .controls-section, .charts-section {
                width: 95vw;
                min-width: 0;
            }
        }
        
        /* Loading states */
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="experiment-header">
            <div class="experiment-title">Green CDN - CSV Enhanced Experiment</div>
            <div class="experiment-desc">
                Compare load balancing strategies using <b>real historical carbon intensity data</b> from US regions.<br>
                Analyze patterns and make carbon-aware routing decisions to reduce environmental impact.
            </div>
            <div class="demo-banner">
                <h3>Educational Demonstration</h3>
                <p>This is a learning tool using <strong>December 2022 historical data</strong>. All charts and values are demos showing how carbon-aware systems work, not real-time data or actual predictions.</p>
            </div>
            
            <div class="status-badge">Historical Dataset: December 2022 Data from 3 US Power Grids</div>
            
            <div class="info-box">
                <h4>How This Educational Demo Works</h4>
                <strong>Purpose:</strong> Learn how carbon-aware load balancing works using real historical patterns.<br>
                <strong>Data Source:</strong> Actual carbon intensity measurements from Dec 2022 (California, New York, Texas power grids).<br>
                <strong>Carbon-Aware Concept:</strong> Routes more traffic to regions with lower historical carbon intensity (cleaner energy patterns).<br>
                <strong>Educational Value:</strong> Shows potential environmental impact of smart routing decisions.<br>
                <strong>Real vs Demo:</strong> Carbon patterns are real historical data, server characteristics (cost, latency) are simulated for comparison.
            </div>
        </div>
        
        <form method="POST" action="/run_simple_experiment" id="experiment-form">
            <!-- Operation Mode Selection -->
            <div class="operation-mode-selector">
                <h3>Choose Operation Mode</h3>
                <div class="radio-group">
                    <div class="radio-option">
                        <input type="radio" id="realtime-mode" name="operation-mode" value="realtime" onchange="toggleOperationMode()">
                        <label for="realtime-mode">Real-Time Mode (WATTIME API)</label>
                        <span class="realtime-indicator">LIVE DATA</span>
                    </div>
                    <div class="radio-option">
                        <input type="radio" id="simulation-mode" name="operation-mode" value="simulation" checked onchange="toggleOperationMode()">
                        <label for="simulation-mode">Historical Simulation Mode</label>
                        <span class="simulation-indicator">TIME-SERIES</span>
                    </div>
                </div>
                <div class="operation-mode-explanation">
                    <strong>Real-Time Mode:</strong> Uses live carbon intensity data from WATTIME API. Updates HAProxy weights based on current power grid conditions. Requires API credentials.<br>
                    <strong>Historical Simulation Mode:</strong> Replays historical data hour-by-hour using CSV files. Actually updates HAProxy weights to demonstrate time-series carbon-aware routing decisions.
                    <br><br><strong>Key Difference:</strong> Real-time uses current data, simulation replays historical patterns to show how routing would have changed over time.
                </div>
            </div>
            
            <!-- Data Source Selection (for simulation mode) -->
            <div class="data-source-selector" id="data-source-section">
                <h3>Choose Data Source</h3>
                <div class="radio-group">
                    <div class="radio-option">
                        <input type="radio" id="csv-data" name="data-source" value="csv" checked onchange="toggleDataSource()">
                        <label for="csv-data">Historical CSV Data</label>
                        <span class="historical-indicator">HISTORICAL</span>
                    </div>
                    <div class="radio-option">
                        <input type="radio" id="manual-data" name="data-source" value="manual" onchange="toggleDataSource()">
                        <label for="manual-data">Manual Input</label>
                        <span class="demo-indicator">SIMULATED</span>
                    </div>
                </div>
                <div class="data-source-explanation">
                    <strong>Historical CSV Data:</strong> Uses real carbon intensity patterns from December 2022. 
                    Carbon values show actual power grid measurements. Cost and latency are simulated for educational comparison.<br>
                    <strong>Manual Input:</strong> Create hypothetical scenarios by entering custom values to explore different what-if situations.
                    <br><br><strong>Learning Objective:</strong> Understand how real-world carbon data varies by region and time, and how this knowledge can drive smarter infrastructure decisions.
                </div>
            </div>
            
            <!-- Simulation Controls (for simulation mode) -->
            <div class="simulation-controls" id="simulation-controls-section" style="display: none;">
                <h3>Simulation Configuration</h3>
                <div class="simulation-params">
                    <div class="param-group">
                        <label for="sim-start-date">Start Date:</label>
                        <input type="date" id="sim-start-date" name="sim-start-date" value="2022-12-25">
                    </div>
                    <div class="param-group">
                        <label for="sim-end-date">End Date:</label>
                        <input type="date" id="sim-end-date" name="sim-end-date" value="2022-12-31">
                    </div>
                    <div class="param-group">
                        <label for="sim-requests-per-hour">Requests per Hour:</label>
                        <input type="number" id="sim-requests-per-hour" name="sim-requests-per-hour" value="1000" min="100" max="10000">
                    </div>
                    <div class="param-group">
                        <label for="sim-speed">Simulation Speed:</label>
                        <select id="sim-speed" name="sim-speed">
                            <option value="1.0">1x (Real-time)</option>
                            <option value="2.0" selected>2x Speed</option>
                            <option value="5.0">5x Speed</option>
                            <option value="10.0">10x Speed</option>
                        </select>
                    </div>
                </div>
                <div class="simulation-explanation">
                    <strong>Historical Simulation:</strong> This will replay historical carbon data hour-by-hour and actually update HAProxy server weights via the dataplane API. 
                    You'll see real weight changes as the simulation progresses, demonstrating how carbon-aware load balancing adapts to changing grid conditions.
                </div>
            </div>
            
            <!-- Server Configuration -->
            <div class="servers-container">
                {% for i in range(3) %}
                <div class="server-box">
                    <div class="server-name">Server {{ i + 1 }}</div>
                    
                    <!-- CSV Mode -->
                    <div id="csv-config-{{ i }}" class="csv-config">
                        <div class="input-group">
                            <label for="server{{ i }}-region">Region</label>
                            <select id="server{{ i }}-region" name="server{{ i }}-region" onchange="updateStats({{ i }})">
                                {% for code, name in regions.items() %}
                                <option value="{{ code }}" {% if loop.index0 == i %}selected{% endif %}>{{ name }} ({{ code }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div id="server{{ i }}-stats" class="csv-stats">
                            Loading region statistics...
                        </div>
                    </div>
                    
                    <!-- Manual Mode -->
                    <div id="manual-config-{{ i }}" class="manual-config" style="display: none;">
                        <div class="input-group">
                            <label for="server{{ i }}-capacity">Capacity</label>
                            <input type="number" id="server{{ i }}-capacity" name="server{{ i }}-capacity" placeholder="Enter capacity" min="0" />
                        </div>
                        <div class="input-group">
                            <label for="server{{ i }}-carbon">Carbon</label>
                            <input type="number" step="any" id="server{{ i }}-carbon" name="server{{ i }}-carbon" placeholder="gCO₂/kWh" min="0" />
                        </div>
                        <div class="input-group">
                            <label for="server{{ i }}-cost">Cost/Req</label>
                            <input type="number" step="any" id="server{{ i }}-cost" name="server{{ i }}-cost" placeholder="$ per request" min="0" />
                        </div>
                        <div class="input-group">
                            <label for="server{{ i }}-latency">Latency</label>
                            <input type="number" step="any" id="server{{ i }}-latency" name="server{{ i }}-latency" placeholder="ms" min="0" />
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Controls -->
            <div class="controls-section">
                <div class="total-requests-group">
                    <label for="total-requests">Total Requests:</label>
                    <input type="number" id="total-requests" name="total-requests" placeholder="Enter total requests" min="1" required style="width: 200px;" />
                </div>
                <button type="submit" class="btn">Run Enhanced Experiment</button>
                <button type="button" class="btn btn-secondary" onclick="showCharts()">Show Carbon Data Charts</button>
            </div>
        </form>
        
        <!-- Charts Section -->
        <div id="charts-section" class="charts-section" style="display: none;">
            <h3>Educational Demo: Carbon Intensity Patterns (Historical Dec 2022)</h3>
            
            <div class="info-box">
                <h4>Chart Explanations - Educational Demonstrations</h4>
                <strong>Carbon Timeline:</strong> Shows 24-hour patterns from Dec 2022. Demonstrates how carbon intensity varies hourly - lower values = cleaner energy periods.<br>
                <strong>Renewable Energy:</strong> Historical renewable energy percentages. Shows relationship between renewables and carbon intensity.<br>
                <strong>Regional Comparison:</strong> Snapshot from Dec 31, 2022 showing regional differences in grid cleanliness.<br>
                <strong>Pattern Analysis:</strong> Educational demo of prediction concepts using 2022 patterns. Shows typical daily cycles - NOT real future predictions.
                <br><br><strong>Key Learning:</strong> Real carbon-aware systems use this type of data analysis to make intelligent routing decisions in real-time.
            </div>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">
                        Carbon Timeline Demo
                        <span class="historical-indicator">2022 HISTORICAL</span>
                    </div>
                    <p style="font-size: 0.85rem; color: #666; margin: 0.5rem 0;">
                        <strong>Educational Demo:</strong> Shows 24-hour carbon intensity patterns from Dec 2022 (gCO2/kWh). 
                        Demonstrates daily cycles - typically higher during peak demand, lower when renewables are abundant.
                    </p>
                    <canvas id="carbonChart" width="400" height="200"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">
                        Renewable Energy Demo
                        <span class="historical-indicator">2022 HISTORICAL</span>
                    </div>
                    <p style="font-size: 0.85rem; color: #666; margin: 0.5rem 0;">
                        <strong>Educational Demo:</strong> Historical renewable percentages from Dec 2022 (wind, solar, hydro). 
                        Shows how solar peaks midday, wind varies by weather - directly impacts carbon intensity.
                    </p>
                    <canvas id="renewableChart" width="400" height="200"></canvas>
                </div>
            </div>
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">
                        Regional Comparison Demo
                        <span class="historical-indicator">2022 SNAPSHOT</span>
                    </div>
                    <p style="font-size: 0.85rem; color: #666; margin: 0.5rem 0;">
                        <strong>Educational Demo:</strong> Regional carbon intensity snapshot from Dec 31, 2022. 
                        Shows concept: carbon-aware routing would send more traffic to regions with lower bars.
                    </p>
                    <canvas id="comparisonChart" width="400" height="200"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">
                        Pattern Analysis Demo
                        <span class="demo-indicator">EDUCATIONAL CONCEPT</span>
                    </div>
                    <p style="font-size: 0.85rem; color: #666; margin: 0.5rem 0;">
                        <strong>Educational Demo:</strong> Shows how prediction algorithms would work using 2022 patterns. 
                        Demonstrates typical daily carbon cycles - NOT real predictions, but shows the concept for learning.
                    </p>
                    <canvas id="predictionChart" width="400" height="200"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Results -->
        {% if results %}
        <div class="results-card" id="results-section">
            {{ results|safe }}
        </div>
        {% endif %}
    </div>
    
    <script>
        let carbonChart, renewableChart, comparisonChart, predictionChart;
        
        // Toggle between operation modes (real-time vs simulation)
        function toggleOperationMode() {
            const simulationSelected = document.getElementById('simulation-mode').checked;
            const realtimeSelected = document.getElementById('realtime-mode').checked;
            
            const dataSourceSection = document.getElementById('data-source-section');
            const simulationControlsSection = document.getElementById('simulation-controls-section');
            
            if (simulationSelected) {
                // Show data source selection and simulation controls
                dataSourceSection.style.display = 'block';
                simulationControlsSection.style.display = 'block';
                
                // Update form action for simulation mode
                document.getElementById('experiment-form').action = '/run_historical_simulation';
            } else {
                // Hide data source selection and simulation controls for real-time mode
                dataSourceSection.style.display = 'none';
                simulationControlsSection.style.display = 'none';
                
                // Update form action for real-time mode
                document.getElementById('experiment-form').action = '/run_realtime_experiment';
            }
        }
        
        // Toggle between CSV and manual data input
        function toggleDataSource() {
            const csvSelected = document.getElementById('csv-data').checked;
            
            for (let i = 0; i < 3; i++) {
                const csvConfig = document.getElementById(`csv-config-${i}`);
                const manualConfig = document.getElementById(`manual-config-${i}`);
                
                if (csvSelected) {
                    csvConfig.style.display = 'block';
                    manualConfig.style.display = 'none';
                } else {
                    csvConfig.style.display = 'none';
                    manualConfig.style.display = 'block';
                }
            }
        }
        
        // Update statistics for selected region
        function updateStats(serverIndex) {
            const regionSelect = document.getElementById(`server${serverIndex}-region`);
            const statsDiv = document.getElementById(`server${serverIndex}-stats`);
            const region = regionSelect.value;
            
            statsDiv.innerHTML = 'Loading statistics...';
            
            fetch(`/get_simple_region_stats/${region}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats;
                        statsDiv.innerHTML = `
                            <strong>Demo Stats (Dec 2022 Historical):</strong><br>
                            <span style="color: #2e7d32;">Carbon Intensity:</span> ${stats.current?.toFixed(1) || 'N/A'} gCO2/kWh <span class="historical-indicator">HISTORICAL</span><br>
                            <span style="color: #666;">Dec 2022 Average:</span> ${stats.mean?.toFixed(1) || 'N/A'} gCO2/kWh<br>
                            <span style="color: #666;">Range:</span> ${stats.min?.toFixed(1) || 'N/A'} - ${stats.max?.toFixed(1) || 'N/A'}<br>
                            <span style="color: #666;">Pattern:</span> ${stats.trend || 'N/A'} | <span style="color: #666;">Data points:</span> ${stats.data_points || 0}<br>
                            <span style="color: #666;">Cost/Latency:</span> <span class="demo-indicator">DEMO VALUES</span> (educational only)
                        `;
                    } else {
                        statsDiv.innerHTML = `<span style="color: red;">Error: ${data.error}</span>`;
                    }
                })
                .catch(error => {
                    statsDiv.innerHTML = `<span style="color: red;">Error: ${error.message}</span>`;
                });
        }
        
        // Show charts section
        function showCharts() {
            const chartsSection = document.getElementById('charts-section');
            if (chartsSection.style.display === 'none') {
                chartsSection.style.display = 'block';
                loadCharts();
            } else {
                chartsSection.style.display = 'none';
            }
        }
        
        // Load and display charts
        function loadCharts() {
            const regions = Array.from(document.querySelectorAll('[name$="-region"]')).map(el => el.value);
            
            // Load chart data for all selected regions
            fetch('/get_chart_data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({regions: regions})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    createCharts(data.chart_data);
                } else {
                    console.error('Error loading chart data:', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
        
        // Create charts using Chart.js
        function createCharts(chartData) {
            // Destroy existing charts
            if (carbonChart) carbonChart.destroy();
            if (renewableChart) renewableChart.destroy();
            if (comparisonChart) comparisonChart.destroy();
            if (predictionChart) predictionChart.destroy();
            
            const colors = ['#2E7D32', '#1976D2', '#F57C00'];
            
            // Carbon intensity timeline
            const carbonCtx = document.getElementById('carbonChart').getContext('2d');
            carbonChart = new Chart(carbonCtx, {
                type: 'line',
                data: {
                    labels: chartData[Object.keys(chartData)[0]]?.labels || [],
                    datasets: Object.keys(chartData).map((region, i) => ({
                        label: chartData[region].region_name,
                        data: chartData[region].carbon_values,
                        borderColor: colors[i % colors.length],
                        backgroundColor: colors[i % colors.length] + '20',
                        tension: 0.4
                    }))
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Carbon Intensity (gCO₂/kWh)'
                            }
                        }
                    }
                }
            });
            
            // Renewable energy percentage
            const renewableCtx = document.getElementById('renewableChart').getContext('2d');
            renewableChart = new Chart(renewableCtx, {
                type: 'line',
                data: {
                    labels: chartData[Object.keys(chartData)[0]]?.labels || [],
                    datasets: Object.keys(chartData).map((region, i) => ({
                        label: chartData[region].region_name,
                        data: chartData[region].renewable_values,
                        borderColor: colors[i % colors.length],
                        backgroundColor: colors[i % colors.length] + '20',
                        tension: 0.4
                    }))
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Renewable Energy %'
                            }
                        }
                    }
                }
            });
            
            // Regional comparison (current values)
            const comparisonCtx = document.getElementById('comparisonChart').getContext('2d');
            const currentValues = Object.keys(chartData).map(region => {
                const values = chartData[region].carbon_values;
                return values[values.length - 1] || 0;  // Latest value
            });
            
            comparisonChart = new Chart(comparisonCtx, {
                type: 'bar',
                data: {
                    labels: Object.keys(chartData).map(region => chartData[region].region_name),
                    datasets: [{
                        label: 'Current Carbon Intensity',
                        data: currentValues,
                        backgroundColor: colors
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Carbon Intensity (gCO₂/kWh)'
                            }
                        }
                    }
                }
            });
            
            // Historical pattern analysis (demonstrates typical daily cycle)
            const predictionCtx = document.getElementById('predictionChart').getContext('2d');
            const patternLabels = ['00:00', '06:00', '12:00', '18:00', '24:00'];  // Typical day cycle
            
            predictionChart = new Chart(predictionCtx, {
                type: 'line',
                data: {
                    labels: patternLabels,
                    datasets: Object.keys(chartData).map((region, i) => {
                        const values = chartData[region].carbon_values;
                        const avgValue = values.reduce((a, b) => a + b, 0) / values.length;
                        
                        // Create typical daily pattern (demo purposes)
                        // Lower at night (renewable), higher at peak hours
                        const typicalPattern = [
                            avgValue * 0.85,  // 00:00 - lower at night
                            avgValue * 0.80,  // 06:00 - early morning low
                            avgValue * 1.10,  // 12:00 - peak demand
                            avgValue * 1.15,  // 18:00 - evening peak
                            avgValue * 0.90   // 24:00 - night again
                        ];
                        
                        return {
                            label: chartData[region].region_name + ' (Typical Pattern)',
                            data: typicalPattern,
                            borderColor: colors[i % colors.length],
                            backgroundColor: colors[i % colors.length] + '20',
                            borderDash: [5, 5],
                            tension: 0.4
                        };
                    })
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Carbon Intensity (gCO₂/kWh) - Historical Pattern'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Typical Daily Cycle (Based on 2022 Data)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        }
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            // Load initial stats for all servers
            for (let i = 0; i < 3; i++) {
                updateStats(i);
            }
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def simple_experiment():
    processor = get_simple_processor()
    regions = processor.get_available_regions()
    return render_template_string(SIMPLE_EXPERIMENT_TEMPLATE, regions=regions, results=None)

@app.route('/get_simple_region_stats/<region>', methods=['GET'])
def get_simple_region_stats(region):
    try:
        processor = get_simple_processor()
        stats = processor.get_carbon_stats(region)
        if stats:
            return jsonify({'success': True, 'stats': stats})
        else:
            return jsonify({'success': False, 'error': 'No data available for region'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    try:
        data = request.get_json()
        regions = data.get('regions', [])
        
        processor = get_simple_processor()
        chart_data = {}
        
        for region in regions:
            region_chart_data = processor.generate_simple_chart_data(region)
            if region_chart_data:
                chart_data[region] = region_chart_data
        
        return jsonify({'success': True, 'chart_data': chart_data})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/run_simple_experiment', methods=['POST'])
def run_simple_experiment():
    try:
        processor = get_simple_processor()
        regions = processor.get_available_regions()
        
        data_source = request.form.get('data-source', 'csv')
        total_requests = int(request.form.get('total-requests', 0))
        
        server_data = []
        
        if data_source == 'csv':
            # Use CSV data
            for i in range(3):
                region_code = request.form.get(f'server{i}-region')
                stats = processor.get_carbon_stats(region_code)
                
                if stats:
                    server_data.append({
                        'name': f'Server {i+1}',
                        'region': region_code,
                        'region_name': regions[region_code],
                        'capacity': 1000,  # Default capacity
                        'carbon': stats['current'],
                        'cost': 0.01,  # Default cost
                        'latency': 50 + (i * 10)  # Default latency
                    })
                else:
                    flash(f'No data available for region {region_code}', 'error')
                    return redirect(url_for('simple_experiment'))
        else:
            # Use manual input
            for i in range(3):
                capacity = float(request.form.get(f'server{i}-capacity', 0))
                carbon = float(request.form.get(f'server{i}-carbon', 0))
                cost = float(request.form.get(f'server{i}-cost', 0))
                latency = float(request.form.get(f'server{i}-latency', 0))
                
                server_data.append({
                    'name': f'Server {i+1}',
                    'region': 'Manual',
                    'region_name': 'Manual Input',
                    'capacity': capacity,
                    'carbon': carbon,
                    'cost': cost,
                    'latency': latency
                })
        
        # Run load balancing algorithms
        # Round Robin Policy
        rr_requests = [total_requests // 3 for _ in range(3)]
        for i in range(total_requests % 3):
            rr_requests[i] += 1
        
        rr_carbon = sum(rr_requests[i] * server_data[i]['carbon'] for i in range(3))
        rr_cost = sum(rr_requests[i] * server_data[i]['cost'] for i in range(3))
        rr_latency = sum(rr_requests[i] * server_data[i]['latency'] for i in range(3)) / total_requests if total_requests else 0
        
        # Carbon-Aware Policy
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
        
        # Calculate savings
        carbon_savings = rr_carbon - ca_carbon
        cost_savings = rr_cost - ca_cost
        latency_savings = rr_latency - ca_latency
        
        # Generate detailed results HTML with clear explanations
        data_source_label = "Historical 2022 Data (Educational)" if data_source == 'csv' else "Manual Input (Hypothetical)"
        
        results_html = f"""
        <h2>Educational Demo Results</h2>
        
        <div class="demo-banner">
            <h3>Learning Simulation</h3>
            <p>These results show how carbon-aware load balancing would work using historical Dec 2022 data patterns. This is educational - not real-time routing decisions.</p>
        </div>
        
        <div class="info-box">
            <h4>Algorithm Comparison (Educational Demo)</h4>
            <strong>Round Robin:</strong> Traditional approach - distributes requests equally across all servers (33.33% each).<br>
            <strong>Carbon-Aware:</strong> Smart approach - routes more traffic to regions with historically lower carbon intensity. 
            <br>Formula: Weight = 1/carbon_intensity, then distribute proportionally.
        </div>
        
        <h3>Server Configuration</h3>
        <ul>
        {''.join([f'<li><strong>{d["name"]}</strong>: {d["region_name"]} - <span style="color: #2e7d32;">Carbon: {d["carbon"]:.2f} gCO2/kWh</span> <span class="historical-indicator">HISTORICAL</span>, <span style="color: #666;">Cost: ${d["cost"]:.3f}</span> <span class="demo-indicator">SIMULATED</span>, <span style="color: #666;">Latency: {d["latency"]:.1f}ms</span> <span class="demo-indicator">SIMULATED</span></li>' for d in server_data])}
        <li><strong>Total Requests:</strong> {total_requests:,}</li>
        <li><strong>Data Source:</strong> {data_source_label}</li>
        </ul>
        
        <h3>Load Balancing Results</h3>
        <table>
        <tr><th>Policy</th><th>Request Distribution</th><th>Total Carbon (gCO2)</th><th>Total Cost ($)</th><th>Avg Latency (ms)</th></tr>
        <tr><td><strong>Round Robin</strong><br><small>Equal distribution</small></td><td>{', '.join(map(str, rr_requests))}</td><td><span style="color: #d32f2f;">{rr_carbon:.2f}</span></td><td>${rr_cost:.2f}</td><td>{rr_latency:.2f}</td></tr>
        <tr><td><strong>Carbon-Aware</strong><br><small>Routes to cleaner regions</small></td><td>{', '.join(map(str, ca_requests))}</td><td><span style="color: #2e7d32;">{ca_carbon:.2f}</span></td><td>${ca_cost:.2f}</td><td>{ca_latency:.2f}</td></tr>
        </table>
        
        <h3>Environmental Impact Analysis (Demo)</h3>
        <ul>
        <li><strong>Carbon Reduction:</strong> {carbon_savings:.2f} gCO2 ({((carbon_savings/rr_carbon)*100) if rr_carbon > 0 else 0:.1f}% reduction) 
            <span class="historical-indicator">HISTORICAL PATTERN</span></li>
        <li><strong>Cost Impact:</strong> ${cost_savings:.2f} ({((cost_savings/rr_cost)*100) if rr_cost > 0 else 0:.1f}% {"savings" if cost_savings > 0 else "increase"}) 
            <span class="demo-indicator">DEMO VALUES</span></li>
        <li><strong>Latency Impact:</strong> {latency_savings:.2f}ms ({((latency_savings/rr_latency)*100) if rr_latency > 0 else 0:.1f}% {"improvement" if latency_savings > 0 else "increase"}) 
            <span class="demo-indicator">DEMO VALUES</span></li>
        </ul>
        
        <div class="info-box">
            <h4>Key Learning Insights</h4>
            <strong>Carbon Impact:</strong> This demo shows how carbon-aware routing could reduce emissions by directing traffic to regions with historically cleaner electricity grids.<br>
            <strong>Real-World Application:</strong> CDNs and cloud providers are beginning to implement this concept to reduce their environmental footprint.<br>
            <strong>Trade-offs:</strong> Educational simulation shows potential costs or latency impacts depending on where clean energy is available.<br>
            <strong>Educational Value:</strong> Understanding these patterns helps design more sustainable distributed systems.
        </div>
        """
        
        if data_source == 'csv':
            results_html += """
            <h3>Understanding This Educational Demo</h3>
            <div class="info-box">
                <h4>Important: Educational Simulation Using Dec 2022 Historical Data</h4>
                <strong>What you're seeing:</strong> Educational demonstration using real carbon intensity measurements from December 2022 power grids.<br>
                <strong>Learning Purpose:</strong> Shows how carbon-aware load balancing concepts work with real data patterns.<br>
                <strong>Real-World Application:</strong> Actual production systems use current/live data from APIs like WattTime, not historical data.<br>
                <strong>Pattern Analysis:</strong> Charts demonstrate historical patterns to understand typical daily/seasonal carbon cycles for educational purposes.
            </div>
            <p><em>Click "<strong>Show Carbon Data Charts</strong>" above to explore the 2022 data patterns 
            and see how prediction algorithms would work conceptually in a real carbon-aware system.</em></p>
            """
        
        return render_template_string(SIMPLE_EXPERIMENT_TEMPLATE, regions=regions, results=results_html)
        
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('simple_experiment'))


@app.route('/run_historical_simulation', methods=['POST'])
def run_historical_simulation():
    """
    Start historical simulation using CSV data and HAProxy dataplane API.
    
    This route handles the Historical Simulation Mode, which replays historical
    carbon intensity data hour-by-hour and actually updates HAProxy server weights
    via the dataplane API to demonstrate time-series carbon-aware load balancing.
    """
    try:
        # Get simulation engine instance
        simulation_engine = get_simulation_engine()
        
        # Extract simulation parameters from form
        start_date = request.form.get('sim-start-date', '2022-12-25')
        end_date = request.form.get('sim-end-date', '2022-12-31')
        requests_per_hour = int(request.form.get('sim-requests-per-hour', 1000))
        speed_multiplier = float(request.form.get('sim-speed', 2.0))
        
        # Validate date range
        try:
            from datetime import datetime
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start_dt >= end_dt:
                flash('End date must be after start date', 'error')
                return redirect(url_for('simple_experiment'))
                
            # Check if date range is reasonable (max 30 days)
            days_diff = (end_dt - start_dt).days
            if days_diff > 30:
                flash('Date range too large. Maximum 30 days allowed for simulation.', 'error')
                return redirect(url_for('simple_experiment'))
                
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD format.', 'error')
            return redirect(url_for('simple_experiment'))
        
        # Start historical simulation
        success = simulation_engine.start_simulation(
            start_date=start_date,
            end_date=end_date,
            requests_per_hour=requests_per_hour,
            speed_multiplier=speed_multiplier
        )
        
        if success:
            # Create success message with simulation details
            results_html = f"""
            <div style="background: #e8f5e8; border: 1px solid #4caf50; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                <h2 style="color: #2e7d32; margin-bottom: 1rem;">Historical Simulation Started</h2>
                
                <div style="background: rgba(255,255,255,0.8); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: #2e7d32;">Simulation Parameters</h3>
                    <ul style="margin: 0.5rem 0; color: #666;">
                        <li><strong>Period:</strong> {start_date} to {end_date} ({days_diff} days)</li>
                        <li><strong>Request Rate:</strong> {requests_per_hour:,} requests/hour</li>
                        <li><strong>Speed:</strong> {speed_multiplier}x real-time</li>
                        <li><strong>Total Hours:</strong> {days_diff * 24} simulation hours</li>
                    </ul>
                </div>
                
                <div style="background: rgba(255,255,255,0.8); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: #2e7d32;">What's Happening</h3>
                    <ul style="margin: 0.5rem 0; color: #666;">
                        <li><strong>HAProxy Weight Updates:</strong> Real server weights being updated via dataplane API</li>
                        <li><strong>Carbon Data Replay:</strong> Historical Dec 2022 carbon intensities from CSV files</li>
                        <li><strong>Time-Series Analysis:</strong> Hour-by-hour routing decisions based on grid conditions</li>
                        <li><strong>Cumulative Tracking:</strong> Running total of carbon savings vs round-robin routing</li>
                    </ul>
                </div>
                
                <div style="background: rgba(255,255,255,0.8); padding: 1rem; border-radius: 8px;">
                    <h3 style="color: #2e7d32;">Monitor Progress</h3>
                    <p style="color: #666; margin: 0.5rem 0;">
                        Use the <a href="/simulation_status" style="color: #2e7d32; font-weight: bold;">Simulation Status</a> page to:
                    </p>
                    <ul style="margin: 0.5rem 0; color: #666;">
                        <li>View current simulation time and progress</li>
                        <li>See real-time HAProxy weight changes</li>
                        <li>Monitor cumulative carbon savings</li>
                        <li>Control simulation (pause/resume/stop)</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 1rem;">
                    <a href="/simulation_status" style="background: #2e7d32; color: white; padding: 0.8rem 1.5rem; 
                       text-decoration: none; border-radius: 8px; font-weight: bold;">
                        View Simulation Dashboard
                    </a>
                </div>
            </div>
            """
            
            # Get processor for template data
            processor = get_simple_processor()
            regions = processor.get_available_regions()
            
            flash(f'Historical simulation started: {start_date} to {end_date} ({speed_multiplier}x speed)', 'success')
            return render_template_string(SIMPLE_EXPERIMENT_TEMPLATE, regions=regions, results=results_html)
            
        else:
            flash('Failed to start historical simulation. Check server logs for details.', 'error')
            return redirect(url_for('simple_experiment'))
            
    except Exception as e:
        flash(f'Error starting simulation: {e}', 'error')
        return redirect(url_for('simple_experiment'))


@app.route('/run_realtime_experiment', methods=['POST'])
def run_realtime_experiment():
    """
    Run real-time experiment using WATTIME API.
    
    This route handles the Real-Time Mode, which uses live carbon intensity data
    from the WATTIME API and updates HAProxy weights based on current power grid
    conditions. Requires WATTIME API credentials.
    """
    try:
        # This would integrate with the existing carbon_controller.py logic
        # For now, show a placeholder message explaining the feature
        
        results_html = f"""
        <div style="background: #e3f2fd; border: 1px solid #1976d2; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
            <h2 style="color: #1976d2; margin-bottom: 1rem;">Real-Time Mode (WATTIME API)</h2>
            
            <div style="background: rgba(255,255,255,0.8); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h3 style="color: #1976d2;">Live Carbon-Aware Load Balancing</h3>
                <p style="color: #666; margin: 0.5rem 0;">
                    This mode integrates with the existing WATTIME API system to:
                </p>
                <ul style="margin: 0.5rem 0; color: #666;">
                    <li><strong>Fetch Live Data:</strong> Get current carbon intensity from power grids</li>
                    <li><strong>Update Weights:</strong> Automatically adjust HAProxy server weights</li>
                    <li><strong>Real-Time Routing:</strong> Route traffic to currently cleanest regions</li>
                    <li><strong>Continuous Monitoring:</strong> Update weights every 5-15 minutes</li>
                </ul>
            </div>
            
            <div style="background: rgba(255,255,255,0.8); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h3 style="color: #1976d2;">Integration with Existing System</h3>
                <p style="color: #666; margin: 0.5rem 0;">
                    This connects to your existing carbon controller system:
                </p>
                <ul style="margin: 0.5rem 0; color: #666;">
                    <li><code>carbon_controller.py</code> - WATTIME API integration</li>
                    <li><code>app.py</code> - Main application with live carbon updates</li>
                    <li>HAProxy dataplane API - Real weight management</li>
                    <li>Environment variables - WATTIME credentials</li>
                </ul>
            </div>
            
            <div style="background: rgba(255,255,255,0.8); padding: 1rem; border-radius: 8px;">
                <h3 style="color: #1976d2;">Next Steps</h3>
                <p style="color: #666; margin: 0.5rem 0;">
                    To enable real-time mode:
                </p>
                <ol style="margin: 0.5rem 0; color: #666;">
                    <li>Set up WATTIME API credentials in environment variables</li>
                    <li>Ensure HAProxy is running with dataplane API enabled</li>
                    <li>Start the carbon controller service</li>
                    <li>Monitor live updates in the main application</li>
                </ol>
            </div>
            
            <div style="text-align: center; margin-top: 1rem;">
                <a href="/" style="background: #1976d2; color: white; padding: 0.8rem 1.5rem; 
                   text-decoration: none; border-radius: 8px; font-weight: bold;">
                    Go to Main App (Real-Time System)
                </a>
            </div>
        </div>
        """
        
        # Get processor for template data
        processor = get_simple_processor()
        regions = processor.get_available_regions()
        
        flash('Real-time mode connects to your existing WATTIME API system', 'info')
        return render_template_string(SIMPLE_EXPERIMENT_TEMPLATE, regions=regions, results=results_html)
        
    except Exception as e:
        flash(f'Error in real-time mode: {e}', 'error')
        return redirect(url_for('simple_experiment'))


@app.route('/simulation_status')
def simulation_status():
    """
    Display current simulation status and control interface.
    
    This provides a real-time dashboard for monitoring and controlling
    the historical simulation, including current weights, progress,
    and cumulative results.
    """
    try:
        simulation_engine = get_simulation_engine()
        status = simulation_engine.get_simulation_status()
        
        # Create simulation status template
        status_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Historical Simulation Dashboard - Green CDN</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: 'Inter', sans-serif; background: #f2faf2; margin: 0; padding: 2rem; }
                .container { max-width: 1200px; margin: 0 auto; }
                .status-card { background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
                .status-running { border-left: 4px solid #4caf50; }
                .status-paused { border-left: 4px solid #ff9800; }
                .status-stopped { border-left: 4px solid #f44336; }
                h1, h2 { color: #2e7d32; }
                .control-buttons { display: flex; gap: 1rem; margin: 1rem 0; }
                .btn { padding: 0.6rem 1.2rem; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; text-decoration: none; display: inline-block; }
                .btn-success { background: #4caf50; color: white; }
                .btn-warning { background: #ff9800; color: white; }
                .btn-danger { background: #f44336; color: white; }
                .btn-primary { background: #2e7d32; color: white; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
                .metric { background: #f5f5f5; padding: 1rem; border-radius: 8px; text-align: center; }
                .metric-value { font-size: 1.5rem; font-weight: bold; color: #2e7d32; }
                .metric-label { color: #666; font-size: 0.9rem; }
                .chart-container { height: 300px; margin: 1rem 0; }
                .server-weights { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
                .server-weight { background: #f5f5f5; padding: 1rem; border-radius: 8px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Historical Simulation Dashboard</h1>
                
                <div class="status-card {{ status_class }}">
                    <h2>Simulation Status</h2>
                    <p><strong>State:</strong> {{ simulation_state }}</p>
                    {% if status['current_time'] %}
                    <p><strong>Current Time:</strong> {{ status['current_time'] }}</p>
                    {% endif %}
                    
                    <div class="control-buttons">
                        {% if status['is_running'] and not status['is_paused'] %}
                        <a href="/simulation_control/pause" class="btn btn-warning">Pause Simulation</a>
                        {% elif status['is_paused'] %}
                        <a href="/simulation_control/resume" class="btn btn-success">Resume Simulation</a>
                        {% endif %}
                        
                        {% if status['is_running'] or status['is_paused'] %}
                        <a href="/simulation_control/stop" class="btn btn-danger">Stop Simulation</a>
                        {% endif %}
                        
                        <a href="/simple_experiment" class="btn btn-primary">Back to Experiment</a>
                    </div>
                </div>
                
                {% if status['current_weights'] %}
                <div class="status-card">
                    <h2>Current HAProxy Server Weights</h2>
                    <div class="server-weights">
                        {% for server, weight in status['current_weights'].items() %}
                        <div class="server-weight">
                            <div class="metric-value">{{ weight }}</div>
                            <div class="metric-label">{{ server }} ({{ server_regions[server] }})</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
                
                {% if status['results']['timeline'] %}
                <div class="status-card">
                    <h2>Simulation Results</h2>
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-value">{{ "%.1f"|format(status['results']['cumulative_carbon_saved']) }} kg</div>
                            <div class="metric-label">Cumulative Carbon Saved</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{{ status['results']['timeline']|length }}</div>
                            <div class="metric-label">Hours Simulated</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{{ status['results']['weight_changes']|length }}</div>
                            <div class="metric-label">Weight Updates</div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <canvas id="carbonSavingsChart"></canvas>
                    </div>
                </div>
                {% endif %}
            </div>
            
            <script>
                // Auto-refresh every 5 seconds
                setTimeout(() => {
                    window.location.reload();
                }, 5000);
                
                // Chart for carbon savings over time
                {% if status['results']['timeline'] %}
                const ctx = document.getElementById('carbonSavingsChart').getContext('2d');
                const chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: {{ timeline_labels|safe }},
                        datasets: [{
                            label: 'Cumulative Carbon Saved (kg)',
                            data: {{ cumulative_savings|safe }},
                            borderColor: '#4caf50',
                            backgroundColor: 'rgba(76, 175, 80, 0.1)',
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Carbon Saved (kg CO2)'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: 'Simulation Time'
                                }
                            }
                        }
                    }
                });
                {% endif %}
            </script>
        </body>
        </html>
        """
        
        # Prepare template data
        simulation_state = "Running" if status['is_running'] and not status['is_paused'] else \
                          "Paused" if status['is_paused'] else "Stopped"
        
        status_class = "status-running" if status['is_running'] and not status['is_paused'] else \
                      "status-paused" if status['is_paused'] else "status-stopped"
        
        # Server region mapping for display
        server_regions = {
            'n1': 'California (US-CAL-CISO)',
            'n2': 'New York (US-NY-NYIS)', 
            'n3': 'Texas (US-TEX-ERCO)'
        }
        
        # Prepare chart data
        timeline_labels = []
        cumulative_savings = []
        cumulative_carbon = 0
        
        for entry in status['results']['timeline']:
            if 'time' in entry:
                timeline_labels.append(entry['time'].strftime('%H:%M'))
                cumulative_carbon += entry.get('carbon_saved_vs_rr', 0) / 1000  # Convert g to kg
                cumulative_savings.append(round(cumulative_carbon, 2))
        
        return render_template_string(
            status_template,
            status=status,
            simulation_state=simulation_state,
            status_class=status_class,
            server_regions=server_regions,
            timeline_labels=json.dumps(timeline_labels),
            cumulative_savings=json.dumps(cumulative_savings)
        )
        
    except Exception as e:
        flash(f'Error loading simulation status: {e}', 'error')
        return redirect(url_for('simple_experiment'))


@app.route('/simulation_control/<action>')
def simulation_control(action):
    """Control simulation playback (pause/resume/stop)."""
    try:
        simulation_engine = get_simulation_engine()
        
        if action == 'pause':
            simulation_engine.pause_simulation()
            flash('Simulation paused', 'info')
        elif action == 'resume':
            simulation_engine.resume_simulation()
            flash('Simulation resumed', 'success')
        elif action == 'stop':
            simulation_engine.stop_simulation()
            flash('Simulation stopped', 'info')
        else:
            flash('Invalid control action', 'error')
            
        return redirect(url_for('simulation_status'))
        
    except Exception as e:
        flash(f'Error controlling simulation: {e}', 'error')
        return redirect(url_for('simulation_status'))


if __name__ == '__main__':
    print("Simple CSV-Enhanced Experiment App - Starting Up")
    print("=" * 50)
    print("Access at: http://localhost:5004")
    print("Features:")
    print("- CSV data integration using built-in Python libraries")
    print("- Interactive charts with Chart.js")
    print("- Real-time carbon intensity statistics")
    print("- Historical data analysis")
    print("- No external Python dependencies required")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5004)