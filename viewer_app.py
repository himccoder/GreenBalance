#!/usr/bin/env python3
"""
Weight Viewer App - Shows which server has the highest weight
Runs on localhost:5001
"""

from flask import Flask, render_template_string, jsonify
import requests
from requests.auth import HTTPBasicAuth
import json
import time
from datetime import datetime
import logging

app = Flask(__name__)

# Dataplane API configuration (same as manager app)
DATAPLANE_HOST = "haproxy"  # Use container name for Docker networking
DATAPLANE_PORT = 5555
DATAPLANE_USER = "admin"
DATAPLANE_PASS = "password"
BACKEND_NAME = "local_servers"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            logger.error(f"Error getting servers: {e}")
            return None

# Initialize API client
api = DataplaneAPI()

# Server region mapping
server_info = {
    'n1': {'region': 'US West (California)', 'color': '#28a745'},
    'n2': {'region': 'US Central (Texas)', 'color': '#fd7e14'},
    'n3': {'region': 'US East (Mid-Atlantic)', 'color': '#dc3545'}
}

@app.route('/')
def index():
    """Main page showing the server with highest weight"""
    servers = api.get_servers()
    
    if not servers:
        return render_template_string(ERROR_TEMPLATE, 
                                    error="Could not connect to HAProxy Dataplane API")
    
    # Find server with highest weight
    max_weight_server = max(servers, key=lambda s: s['weight'])
    total_weight = sum(s['weight'] for s in servers)
    
    # Calculate percentages
    for server in servers:
        server['percentage'] = (server['weight'] / total_weight * 100) if total_weight > 0 else 0
        server['info'] = server_info.get(server['name'], {
            'region': 'Unknown Region',
            'color': '#6c757d'
        })
    
    # Sort servers by weight (highest first)
    servers.sort(key=lambda s: s['weight'], reverse=True)
    
    return render_template_string(MAIN_TEMPLATE,
                                servers=servers,
                                max_server=max_weight_server,
                                max_server_info=server_info.get(max_weight_server['name'], {
                                    'region': 'Unknown Region',
                                    'color': '#6c757d'
                                }),
                                total_weight=total_weight,
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/api/highest-weight')
def api_highest_weight():
    """API endpoint to get the server with highest weight"""
    servers = api.get_servers()
    
    if not servers:
        return jsonify({"error": "Could not get servers"}), 500
    
    max_weight_server = max(servers, key=lambda s: s['weight'])
    total_weight = sum(s['weight'] for s in servers)
    
    return jsonify({
        "highest_weight_server": max_weight_server,
        "percentage": (max_weight_server['weight'] / total_weight * 100) if total_weight > 0 else 0,
        "total_weight": total_weight,
        "timestamp": datetime.now().isoformat()
    })

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weight Viewer - Green CDN</title>
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
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(34, 139, 34, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(76, 175, 80, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.8) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(34, 139, 34, 0.15);
            border-radius: 24px;
            padding: 2.5rem 2rem;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 1);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(34, 139, 34, 0.05) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .header h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #2e7d32 0%, #4caf50 50%, #1b5e20 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 2px 8px rgba(34, 139, 34, 0.1);
            position: relative;
            z-index: 1;
        }
        
        .timestamp {
            color: #424242;
            font-size: 1rem;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }
        
        .winner-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(34, 139, 34, 0.15);
            border-radius: 24px;
            padding: 3rem 2rem;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 
                0 16px 48px rgba(0, 0, 0, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 1);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .winner-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255, 215, 0, 0.6), transparent);
        }
        
        .winner-card:hover {
            transform: translateY(-5px);
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 1);
        }
        
        .winner-badge {
            font-size: 5rem;
            margin-bottom: 1.5rem;
            text-shadow: 0 4px 8px rgba(255, 215, 0, 0.3);
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .winner-name {
            font-size: 2.8rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 2px 8px rgba(46, 125, 50, 0.2);
        }
        
        .winner-region {
            font-size: 1.4rem;
            color: #424242;
            margin-bottom: 2rem;
            opacity: 0.9;
        }
        
        .winner-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .stat {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat:hover {
            background: rgba(255, 255, 255, 0.95);
            transform: translateY(-3px);
        }
        
        .stat-value {
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #616161;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .servers-list {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
            margin-bottom: 2rem;
        }
        
        .servers-list h3 {
            font-size: 1.6rem;
            font-weight: 600;
            text-align: center;
            margin-bottom: 2rem;
            color: #1b5e20;
            text-shadow: 0 1px 3px rgba(27, 94, 32, 0.1);
        }
        
        .server-item {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .server-item:nth-child(2)::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #ffd700 0%, #ffed4e 100%);
        }
        
        .server-item:nth-child(3)::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #c0c0c0 0%, #e8e8e8 100%);
        }
        
        .server-item:nth-child(4)::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #cd7f32 0%, #daa520 100%);
        }
        
        .server-item:hover {
            background: rgba(255, 255, 255, 0.95);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
        }
        
        .server-name {
            font-weight: 600;
            font-size: 1.2rem;
            color: #1b5e20;
            margin-bottom: 0.25rem;
        }
        
        .server-region {
            font-size: 0.9rem;
            color: #616161;
            opacity: 0.8;
        }
        
        .server-weight {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2e7d32;
            margin-bottom: 0.25rem;
        }
        
        .percentage {
            font-size: 0.9rem;
            color: #4caf50;
            opacity: 0.8;
        }
        
        .refresh-info {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            color: #424242;
            opacity: 0.9;
        }
        
        .refresh-info a {
            color: #2e7d32;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .refresh-info a:hover {
            color: #1b5e20;
            text-shadow: 0 1px 3px rgba(27, 94, 32, 0.2);
        }
        
        /* Toast Notification Styles */
        .toast-container {
            position: fixed;
            top: 2rem;
            right: 2rem;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            pointer-events: none;
        }
        
        .toast {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(34, 139, 34, 0.2);
            border-radius: 16px;
            padding: 1rem 1.5rem;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 1);
            min-width: 300px;
            max-width: 400px;
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: auto;
            position: relative;
            overflow: hidden;
        }
        
        .toast.show {
            transform: translateX(0);
            opacity: 1;
        }
        
        .toast.success {
            border-left: 4px solid #4caf50;
        }
        
        .toast.info {
            border-left: 4px solid #2196f3;
        }
        
        .toast.warning {
            border-left: 4px solid #f57f17;
        }
        
        .toast::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(76, 175, 80, 0.6), transparent);
        }
        
        .toast-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .toast-title {
            font-weight: 600;
            color: #1b5e20;
            font-size: 0.95rem;
        }
        
        .toast-close {
            background: none;
            border: none;
            font-size: 1.2rem;
            color: #616161;
            cursor: pointer;
            padding: 0;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: all 0.2s ease;
        }
        
        .toast-close:hover {
            background: rgba(0, 0, 0, 0.1);
            color: #1b5e20;
        }
        
        .toast-message {
            color: #424242;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        .toast-details {
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            font-size: 0.8rem;
            color: #616161;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 2.5rem;
            }
            
            .winner-name {
                font-size: 2rem;
            }
            
            .winner-stats {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            
            .server-item {
                flex-direction: column;
                text-align: center;
                gap: 1rem;
            }
            
            .winner-badge {
                font-size: 4rem;
            }

            .toast-container {
                top: 1rem;
                right: 1rem;
                left: 1rem;
            }
            
            .toast {
                min-width: auto;
                max-width: none;
            }
        }
    </style>
    <script>
        // Toast notification system
        function showToast(title, message, type = 'info', details = null, duration = 5000) {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            toast.innerHTML = `
                <div class="toast-header">
                    <div class="toast-title">${title}</div>
                    <button class="toast-close" onclick="removeToast(this.parentElement.parentElement)">×</button>
                </div>
                <div class="toast-message">${message}</div>
                ${details ? `<div class="toast-details">${details}</div>` : ''}
            `;
            
            container.appendChild(toast);
            
            // Trigger animation
            setTimeout(() => toast.classList.add('show'), 100);
            
            // Auto remove
            setTimeout(() => removeToast(toast), duration);
            
            return toast;
        }
        
        function removeToast(toast) {
            if (toast && toast.classList) {
                toast.classList.remove('show');
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.parentElement.removeChild(toast);
                    }
                }, 400);
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            // Add smooth entrance animations
            const cards = document.querySelectorAll('.server-item');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });

        // Auto-refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</head>
<body>
    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>
    <div class="container">
        <div class="header">
            <h1>Traffic Leader</h1>
            <div class="timestamp">Last updated: {{ timestamp }}</div>
        </div>
        
        <div class="winner-card">
            <div class="winner-badge">★</div>
            <div class="winner-name">{{ max_server.name|upper }}</div>
            <div class="winner-region">{{ max_server_info.region }}</div>
            
            <div class="winner-stats">
                <div class="stat">
                    <div class="stat-value">{{ max_server.weight }}</div>
                    <div class="stat-label">Weight</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{{ "%.1f"|format(max_server.percentage) }}%</div>
                    <div class="stat-label">Traffic Share</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{{ total_weight }}</div>
                    <div class="stat-label">Total Weight</div>
                </div>
            </div>
        </div>
        
        <div class="servers-list">
            <h3>All Servers (Ranked by Weight)</h3>
            {% for server in servers %}
            <div class="server-item">
                <div>
                    <div class="server-name">{{ server.name|upper }}</div>
                    <div class="server-region">{{ server.info.region }}</div>
                </div>
                <div style="text-align: right;">
                    <div class="server-weight">{{ server.weight }}</div>
                    <div class="percentage">{{ "%.1f"|format(server.percentage) }}%</div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="refresh-info">
            Page refreshes automatically every 30 seconds<br><br>
            Connect to <a href="http://localhost:5000">Weight Manager</a> to make changes
        </div>
    </div>
</body>
</html>
"""

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>❌ Connection Error - Green CDN</title>
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
            position: relative;
            overflow-x: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(34, 139, 34, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(76, 175, 80, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.8) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        
        .error-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(244, 67, 54, 0.2);
            border-radius: 24px;
            padding: 3rem 2rem;
            text-align: center;
            max-width: 500px;
            width: 90%;
            box-shadow: 
                0 16px 48px rgba(0, 0, 0, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 1);
            position: relative;
            overflow: hidden;
        }
        
        .error-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(244, 67, 54, 0.8), transparent);
        }
        
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 20px rgba(255, 107, 107, 0.3);
        }
        
        p {
            color: #424242;
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 1rem;
            opacity: 0.9;
        }
        
        .retry-info {
            background: rgba(255, 215, 0, 0.1);
            border: 1px solid rgba(255, 215, 0, 0.3);
            border-radius: 12px;
            padding: 1rem;
            margin-top: 2rem;
            color: #f57f17;
        }
    </style>
</head>
<body>
    <div class="error-card">
        <h1>Connection Error</h1>
        <p>{{ error }}</p>
        <p>Please ensure HAProxy with Dataplane API is running.</p>
        <div class="retry-info">
            Page will automatically retry in a few seconds
        </div>
    </div>
    
    <script>
        // Auto-retry after 5 seconds
        setTimeout(function() {
            location.reload();
        }, 5000);
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    print("Green CDN Weight Viewer - Starting Up")
    print("=" * 45)
    print("Access at: http://localhost:5001")
    print("Shows server with highest weight")
    print("Auto-refreshes every 30 seconds")
    print("=" * 45)
    print("Ready to display traffic leaders!")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 