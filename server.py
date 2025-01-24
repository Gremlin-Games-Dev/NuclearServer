from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import json
import time
from threading import Thread, Lock

# Create Flask app instances
app_main = Flask(__name__)  # Main app (port 5000)
app_http = Flask(__name__)   # Website app (port 80)
CORS(app_main)
CORS(app_http)

# Shared configurations
CONFIG_FILE = "config.json"
ICON_FILE = "icon.svg"
DATA_DIR = "data"
MAP_FILE = "map.zip"
HEARTBEAT_TIMEOUT = 15

player_heartbeats = {}
lock = Lock()

# Ensure necessary directories and files exist
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"server_name": "Default Server"}, f)


# Main app routes (port 5000)
@app_main.route('/config.json', methods=['GET'])
def get_config():
    if os.path.exists(CONFIG_FILE):
        return send_from_directory('.', CONFIG_FILE)
    return "Config not found", 404

@app_main.route('/map.zip', methods=['GET'])
def get_map():
    if os.path.exists(MAP_FILE):
        return send_from_directory('.', MAP_FILE)
    return "Map not found", 404

@app_main.route('/icon.svg', methods=['GET'])
def get_icon():
    if os.path.exists(ICON_FILE):
        return send_from_directory('.', ICON_FILE)
    return "Icon not found", 404


@app_main.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    player_id = data.get('player_id')
    room_id = data.get('room_id')

    if not player_id or not room_id:
        return "Invalid data", 400

    with lock:
        player_heartbeats[(room_id, player_id)] = time.time()

    return "Heartbeat received", 200

@app_http.route("/real")
def dev_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Development Server - Nuclear</title>
        <style>
            html, body {
                height: 100%;
                margin: 0;
                display: flex;
                flex-direction: column;
                background-color: #000;
                color: #fff;
            }
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
            }
            h1 {
                font-size: 3em;
                color: #ff00ff;
            }
            p {
                font-size: 1.5em;
                margin: 20px 0;
                color: #dd00dd
            }
            footer {
                margin-top: auto;
                font-size: 1.2em;
                color: #ff00ff;
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 20px;
            }
            .logo {
                width: 200px;
                opacity: 0.7;
            }
    </style>
    </head>
    <body>
        <h1>Development Server</h1>
        <p>This server is for the game <strong style="color:lime">Nuclear</strong>, currently under development by <strong>Gremlin Games</strong>.</p>
        <p>Please leave this page immediately and do not interact further in any way.</p>
        <footer>
            <div>&copy; 2025 Gremlin Games. All rights reserved.</div>
            <img src="/gremlingames.png" alt="Gremlin Games Logo" class="logo">
        </footer>
    </body>
    </html>
    """

@app_http.route("/gremlingames.png", methods=['GET'])
def dev_logo():
    if os.path.exists("gremlingames.png"):
        return send_from_directory('.', "gremlingames.png")
    return "Logo not found", 404

#Beginning of Anti-Bot

@app_http.route('/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def reflector(subpath):
    # Log the incoming request
    client_ip = request.remote_addr
    method = request.method
    print(f"Bot detected from {client_ip} using {method} at /{subpath}")

    def delayed_response():
        while True:
            yield "Who's Laughing Now?\n"
            time.sleep(5)

    return Response(delayed_response(), content_type='text/plain')

#End of Anti-Bot

# Cleanup function for the main app
def cleanup():
    while True:
        with lock:
            current_time = time.time()
            for (room_id, player_id), last_heartbeat in list(player_heartbeats.items()):
                if current_time - last_heartbeat > HEARTBEAT_TIMEOUT:
                    player_heartbeats.pop((room_id, player_id), None)
                    player_file = os.path.join(DATA_DIR, room_id, f"{player_id}.json")
                    if os.path.exists(player_file):
                        os.remove(player_file)

            for room_id in os.listdir(DATA_DIR):
                room_path = os.path.join(DATA_DIR, room_id)
                if not os.listdir(room_path):
                    os.rmdir(room_path)

        time.sleep(1)


# Run each Flask app on separate threads
def run_main_app():
    Thread(target=cleanup, daemon=True).start()
    app_main.run(host='0.0.0.0', port=5000)


def run_http_app():
    app_http.run(host='0.0.0.0', port=80)


if __name__ == '__main__':
    thread_main = Thread(target=run_main_app)
    thread_http = Thread(target=run_http_app)

    thread_main.start()
    thread_http.start()

    thread_main.join()
    thread_http.join()