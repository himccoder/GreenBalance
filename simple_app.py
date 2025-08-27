from flask import Flask, jsonify
import random
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    carbon_data = {
        'california': random.randint(200, 400),
        'texas': random.randint(400, 600), 
        'midatlantic': random.randint(500, 700)
    }
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌱 Green CDN Demo</title>
        <style>
            body {{ font-family: Arial; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
            .card {{ background: rgba(255,255,255,0.1); padding: 30px; margin: 20px 0; border-radius: 15px; }}
            .region {{ text-align: center; margin: 20px; display: inline-block; width: 250px; }}
            .carbon-value {{ font-size: 2.5em; font-weight: bold; margin: 15px 0; }}
            .button {{ background: #4CAF50; color: white; padding: 15px 30px; border: none; border-radius: 8px; margin: 10px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h1>🌱 Green CDN - Carbon-Aware Load Balancing</h1>
        
        <div class="card">
            <h2>🌍 Regional Carbon Intensity</h2>
            <div class="region">
                <h3>California</h3>
                <div class="carbon-value" style="color: #4CAF50">{carbon_data['california']}</div>
                <p>g CO₂/kWh</p>
            </div>
            <div class="region">
                <h3>Texas</h3>
                <div class="carbon-value" style="color: #FF9800">{carbon_data['texas']}</div>
                <p>g CO₂/kWh</p>
            </div>
            <div class="region">
                <h3>Mid-Atlantic</h3>
                <div class="carbon-value" style="color: #F44336">{carbon_data['midatlantic']}</div>
                <p>g CO₂/kWh</p>
            </div>
        </div>
        
        <div class="card">
            <h2>🎛️ How It Works</h2>
            <p><strong>Carbon-Aware Routing:</strong> Lower carbon intensity = More traffic</p>
            <button class="button" onclick="location.reload()">🔄 Refresh Data</button>
            <a href="/api/carbon" class="button">📊 View API</a>
        </div>
        
        <div class="card">
            <h2>📊 Current Status</h2>
            <p>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>This demo simulates real-time carbon intensity data and shows how traffic would be distributed.</p>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/api/carbon')
def api_carbon():
    return jsonify({
        'california': random.randint(200, 400),
        'texas': random.randint(400, 600), 
        'midatlantic': random.randint(500, 700),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
