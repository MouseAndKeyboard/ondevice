import os
import time
import threading
import requests
from flask import Flask, render_template, jsonify

# -----------------------------
# Configuration
# -----------------------------

API_BASE = "https://api.affinitycube.com"
DEVICE_NAME = "My Raspberry Pi"
DEVICE_PHOTO_URL = "https://example.com/photo.jpg"  # any relevant photo or placeholder
HEARTBEAT_INTERVAL = 5   # seconds
DEVICE_ID_FILE = "device_id.txt"  # store the device ID locally

app = Flask(__name__)

# In-memory state about inbound calls (for the front end to read)
call_in_progress = False
inbound_call_detected = False


# -----------------------------
# Registration / Heartbeat Logic
# -----------------------------

def load_device_id():
    """Load the device_id from a local file if it exists."""
    if os.path.exists(DEVICE_ID_FILE):
        with open(DEVICE_ID_FILE, "r") as f:
            return f.read().strip()
    return None

def save_device_id(device_id):
    """Save the device_id to a local file."""
    with open(DEVICE_ID_FILE, "w") as f:
        f.write(device_id)

def register_device_if_needed():
    """
    1) GET /devices
    2) Check if this device is already registered.
       If not, POST /devices/register to create an entry.
    3) Return the device_id.
    """
    try:
        r = requests.get(f"{API_BASE}/devices", timeout=5)
        r.raise_for_status()
        devices = r.json()

        local_device_id = load_device_id()
        # Check if local_device_id still appears in the remote list
        if local_device_id and any(d["id"] == local_device_id for d in devices):
            return local_device_id

        # Otherwise, we need to register a new device
        payload = {
            "name": DEVICE_NAME,
            "photo_url": DEVICE_PHOTO_URL
        }
        reg_r = requests.post(f"{API_BASE}/devices/register", json=payload, timeout=5)
        reg_r.raise_for_status()
        new_device = reg_r.json()
        new_device_id = new_device["id"]
        save_device_id(new_device_id)
        return new_device_id

    except requests.RequestException as e:
        print(f"Device registration failed: {e}")
        return None

def heartbeat_loop():
    """
    Periodically POST to /devices/heartbeat/{device_id}.
    Check for inbound call. If inbound call is found:
      - trigger HDMI-CEC script
      - set a flag to update the front end
    """
    global inbound_call_detected

    # Ensure the device is registered
    device_id = register_device_if_needed()
    if not device_id:
        print("Could not register device. Heartbeat loop cannot start.")
        return

    while True:
        try:
            hb_url = f"{API_BASE}/devices/heartbeat/{device_id}"
            r = requests.post(hb_url, timeout=5)
            r.raise_for_status()
            response = r.json()

            # Suppose the JSON indicates inbound_call: true/false
            inbound_call = response.get("inbound_call", False)
            if inbound_call and not inbound_call_detected:
                inbound_call_detected = True
                print("Inbound call detected!")
                # Trigger HDMI-CEC command
                trigger_cec_script()
            elif not inbound_call:
                inbound_call_detected = False

        except requests.RequestException as e:
            print(f"Heartbeat error: {e}")

        time.sleep(HEARTBEAT_INTERVAL)

def trigger_cec_script():
    """
    Delegate any HDMI-CEC commands to a shell script, if desired.
    """
    script_path = os.path.join(os.path.dirname(__file__), "scripts", "trigger_cec.sh")
    os.system(f"sh {script_path}")


# -----------------------------
# Flask Routes
# -----------------------------

@app.route("/")
def index():
    """
    Default route: either show the screensaver
    or (optionally) dynamically switch to "call incoming"
    if inbound call is active. You can also
    do this switching entirely in JavaScript.
    """
    return render_template("index.html")

@app.route("/call_incoming")
def call_incoming_page():
    """
    Simple route that displays the 'call incoming' screen.
    """
    return render_template("call_incoming.html")

@app.route("/status")
def status():
    """
    Returns JSON about current inbound_call state, etc.
    Front end can poll /status periodically to decide
    if it should display the incoming call screen.
    """
    return jsonify({
        "inbound_call": inbound_call_detected
    })


# -----------------------------
# App Entrypoint
# -----------------------------

if __name__ == "__main__":
    # Start the heartbeat loop in a separate thread
    t = threading.Thread(target=heartbeat_loop, daemon=True)
    t.start()

    # Run Flask on port 8888, accessible at localhost:8888
    app.run(host="0.0.0.0", port=8888, debug=True)
