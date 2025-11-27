from flask import Flask, request # global flask installation
from datetime import datetime

app = Flask(__name__)

last_value = None  # global to hold the latest value


@app.post("/sample")
def sample():
    global last_value
    data = request.get_json(force=True, silent=True) or {}
    value = data.get("value")
    timestamp = datetime.now().isoformat(timespec="seconds")

    last_value = (value, timestamp)
    print(f"[{timestamp}] Received value from browser:", value)

    return {"status": "ok"}


@app.get("/latest")
def latest():
    if last_value is None:
        return {"value": None, "timestamp": None}
    value, ts = last_value
    return {"value": value, "timestamp": ts}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
