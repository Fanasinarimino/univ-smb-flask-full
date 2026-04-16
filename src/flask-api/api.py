import os
import json
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Dossier data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

FILES = {
    "lb": os.path.join(DATA_DIR, "loadbalancer.json"),
    "rp": os.path.join(DATA_DIR, "reverseproxy.json"),
    "ws": os.path.join(DATA_DIR, "webserver.json"),
}

# ------------------ UTILITAIRES JSON ------------------

def load_list(kind):
    path = FILES[kind]
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def save_list(kind, items):
    path = FILES[kind]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def next_id(items):
    return max([item.get("id", 0) for item in items], default=0) + 1

# ------------------ ROUTES LOGIN / IDENTITY ------------------

USERS = [
    {"username": "admin", "role": "admin"},
    {"username": "user", "role": "user"}
]

@app.get("/login")
def login():
    return jsonify({"message": "Login OK", "users": USERS})

@app.get("/identity")
def identity_all():
    return jsonify(USERS)

@app.get("/identity/<username>")
def identity_one(username):
    for u in USERS:
        if u["username"] == username:
            return jsonify(u)
    abort(404, "User not found")

# ------------------ ROUTES GÉNÉRIQUES CONFIG ------------------

def get_all(kind):
    return jsonify(load_list(kind))

def create(kind):
    items = load_list(kind)
    data = request.get_json()

    if not isinstance(data, dict):
        abort(400, "JSON object required")

    data["id"] = next_id(items)
    items.append(data)
    save_list(kind, items)
    return jsonify(data), 201

def delete(kind, item_id):
    items = load_list(kind)
    new_items = [i for i in items if i["id"] != item_id]

    if len(new_items) == len(items):
        abort(404, f"{kind} id {item_id} not found")

    save_list(kind, new_items)
    return "", 204

# ------------------ LOAD BALANCER ------------------

@app.get("/config/lb")
def lb_all():
    return get_all("lb")

@app.post("/config/lb")
def lb_create():
    return create("lb")

@app.delete("/config/lb/<int:item_id>")
def lb_delete(item_id):
    return delete("lb", item_id)

# ------------------ REVERSE PROXY ------------------

@app.get("/config/rp")
def rp_all():
    return get_all("rp")

@app.post("/config/rp")
def rp_create():
    return create("rp")

@app.delete("/config/rp/<int:item_id>")
def rp_delete(item_id):
    return delete("rp", item_id)

# ------------------ WEB SERVER ------------------

@app.get("/config/ws")
def ws_all():
    return get_all("ws")

@app.post("/config/ws")
def ws_create():
    return create("ws")

@app.delete("/config/ws/<int:item_id>")
def ws_delete(item_id):
    return delete("ws", item_id)

# ------------------ MAIN ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
