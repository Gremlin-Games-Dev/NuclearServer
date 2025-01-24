from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import json
import time
from threading import Thread, Lock

app_main = Flask(__name__)
CORS(app_main)

CONFIG_FILE = "config.json"
ICON_FILE = "icon.svg"
DATA_DIR = "data"
HEARTBEAT_TIMEOUT = 15

player_heartbeats = {}
lock = Lock()

os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"server_name": "Default Server"}, f)

@app_main.route('/config.json', methods=['GET'])
def get_config():
    if os.path.exists(CONFIG_FILE):
        return send_from_directory('.', CONFIG_FILE)
    return "Config not found", 404

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

Thread(target=cleanup, daemon=True).start()

app_main.run(host='0.0.0.0', port=5000)
