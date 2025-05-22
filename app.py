import os, time, threading, requests
from flask import Flask, render_template, jsonify, redirect, url_for

API_BASE          = os.getenv("API_BASE", "https://api.affinitycube.com")
DEVICE_NAME       = os.getenv("DEVICE_NAME", "WarmHearts")
DEVICE_PHOTO_URL  = os.getenv("DEVICE_PHOTO_URL", "https://example.com/photo.jpg")
HEARTBEAT_INTERVAL= int(os.getenv("HEARTBEAT_INTERVAL", "5"))
DEVICE_ID_FILE    = "device_id.txt"

app = Flask(__name__, static_url_path='/static')

# -------- Runtime state --------
inbound_call_detected = False

# -------- Device registration & heartbeat --------
def load_device_id():
    return open(DEVICE_ID_FILE).read().strip() if os.path.exists(DEVICE_ID_FILE) else None

def save_device_id(device_id):
    with open(DEVICE_ID_FILE, "w") as f: f.write(device_id)

def register_device():
    # 1. fetch list
    try:
        devices = requests.get(f"{API_BASE}/devices", timeout=5).json()
    except Exception as e:
        print("Device list fetch failed:", e); return None

    local_id = load_device_id()
    if local_id and any(d["id"] == local_id for d in devices):
        return local_id                         # already registered

    payload = {"name": DEVICE_NAME, "photo_url": DEVICE_PHOTO_URL}
    try:
        new_device = requests.post(f"{API_BASE}/devices/register",
                                   json=payload, timeout=5).json()
        save_device_id(new_device["id"])
        return new_device["id"]
    except Exception as e:
        print("Registration failed:", e); return None

def heartbeat_loop():
    global inbound_call_detected
    device_id = register_device()
    if not device_id: return

    hb_url = f"{API_BASE}/devices/heartbeat/{device_id}"
    while True:
        try:
            response = requests.post(hb_url, timeout=5).json()
            inbound = response.get("inbound_call", False)
            if inbound and not inbound_call_detected:
                inbound_call_detected = True
                os.system("scripts/trigger_cec.sh")
            elif not inbound:
                inbound_call_detected = False
        except Exception as e:
            print("Heartbeat error:", e)
        time.sleep(HEARTBEAT_INTERVAL)

# -------- Flask routes --------
@app.route("/")
def index():               return render_template("index.html")

@app.route("/call_incoming")
def call_incoming_page():  return render_template("call_incoming.html")

@app.route("/live_call")
def live_call_page():      return render_template("live_call.html")

@app.route("/status")
def status():              return jsonify(inbound_call=inbound_call_detected)

# -------- main --------
if __name__ == "__main__":
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8888)
