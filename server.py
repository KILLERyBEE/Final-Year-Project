"""
AirNav – server.py
A lightweight Flask backend that bridges the HTML frontend
with the master_gesture_controller.py Python script.

Endpoints:
  POST /start  → launches master_gesture_controller.py
  POST /stop   → kills the running process
  GET  /status → returns whether the process is running

Run this file first, then open Frontend/index.html in your browser.
    python server.py
"""

import subprocess
import sys
import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from the local HTML file

# Path to the master gesture controller script
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MASTER_SCRIPT = os.path.join(BASE_DIR, "master_gesture_controller.py")

# Global reference to the running process
gesture_process = None


@app.route("/start", methods=["POST"])
def start_camera():
    global gesture_process

    # Don't start a second instance if already running
    if gesture_process is not None and gesture_process.poll() is None:
        return jsonify({"status": "already_running", "message": "Gesture controller is already running."}), 200

    try:
        # On Windows: open in a new visible console window
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE

        gesture_process = subprocess.Popen(
            [sys.executable, MASTER_SCRIPT],
            cwd=BASE_DIR,
            **kwargs
        )
        return jsonify({"status": "started", "message": "Gesture controller started successfully."}), 200
    except FileNotFoundError:
        return jsonify({"status": "error", "message": f"Script not found: {MASTER_SCRIPT}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/stop", methods=["POST"])
def stop_camera():
    global gesture_process

    if gesture_process is None or gesture_process.poll() is not None:
        return jsonify({"status": "not_running", "message": "Gesture controller is not running."}), 200

    try:
        gesture_process.terminate()
        gesture_process.wait(timeout=5)
        gesture_process = None
        return jsonify({"status": "stopped", "message": "Gesture controller stopped."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/status", methods=["GET"])
def status():
    global gesture_process
    running = gesture_process is not None and gesture_process.poll() is None
    return jsonify({"running": running}), 200


if __name__ == "__main__":
    print("=" * 50)
    print("  AirNav Backend Server")
    print(f"  Master script: {MASTER_SCRIPT}")
    print("  Running at:    http://localhost:5000")
    print("  Open Frontend/index.html in your browser")
    print("=" * 50)
    app.run(host="localhost", port=5000, debug=False)
