from flask import Flask, render_template_string, request, flash, redirect, url_for

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
            gap: 0.75rem;
        }
        label {
            font-size: 0.9rem;
            min-width: 70px;
            color: #2e7d32;
            font-weight: 600;
            user-select: none;
        }
        input[type="text"] {
            flex-grow: 1;
            padding: 0.35rem 0.6rem;
            border: 1.5px solid #a5d6a7;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s ease-in-out;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #388e3c;
            box-shadow: 0 0 6px #81c784;
        }
        button {
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
        button:hover {
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
        .total-requests-box button {
            padding: 0.6rem 1.2rem;
            font-size: 1.1rem;
            user-select: none;
        }
    </style>
</head>
<body>
    <div class="servers-container">
        {% for server in servers %}
        <div class="server-box">
            <div class="server-name">{{ server.upper() }}</div>
            <form method="POST" action="#" class="input-group" style="margin-bottom: 0.75rem;">
                <label for="{{ server }}-capacity">Capacity</label>
                <input type="text" id="{{ server }}-capacity" name="{{ server }}-capacity" placeholder="Enter capacity" />
                <button type="submit">Set</button>
            </form>
            <form method="POST" action="#" class="input-group">
                <label for="{{ server }}-data">Data</label>
                <input type="text" id="{{ server }}-data" name="{{ server }}-data" placeholder="Enter data" />
                <button type="submit">Set</button>
            </form>
        </div>
        {% endfor %}
    </div>

    <form method="POST" action="#" class="total-requests-box">
        <label for="total-requests">Total Requests</label>
        <input type="text" id="total-requests" name="total-requests" placeholder="Enter total number of requests" />
        <button type="submit">Run</button>
    </form>
</body>
</html>
"""

@app.route('/')
def experiment():
    servers = ['server1', 'server2', 'server3']
    return render_template_string(EXPERIMENT_TEMPLATE, servers=servers)

if __name__ == '__main__':
    print("Experiment App - Starting Up")
    print("=" * 30)
    print("Access at: http://localhost:5002")
    print("Shows three servers with capacity/data inputs and total requests input")
    print("=" * 30)
    app.run(debug=True, host='0.0.0.0', port=5002)