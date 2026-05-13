from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
app.secret_key = "komisureiya_secret_key_2024"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

client = None
client_lock = threading.Lock()


def make_emit(sid):
    def fn(event, data):
        socketio.emit(event, data, to=sid)
    return fn


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/ping")
def ping():
    return "OK", 200


# ── Socket events ──────────────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    with client_lock:
        if client and client.running:
            client.emit = make_emit(request.sid)
            client.push_state()
            for msg in client.log_buffer[-50:]:
                emit("log", {"message": msg})

@socketio.on("login")
def on_login(data):
    global client
    from api_client import ApiClient
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()
    if not email or not password:
        emit("login_result", {"ok": False, "error": "帳號名稱和密碼為必填"})
        return
    try:
        c = ApiClient(email, password, emit_fn=make_emit(request.sid))
        c.login()
        c.connect_ws()
        c.start()
        time.sleep(1)  # Give WebSocket time to connect
        c.join_core()
        with client_lock:
            global client
            client = c
        emit("login_result", {"ok": True})
        c.push_state()
    except Exception as e:
        emit("login_result", {"ok": False, "error": str(e)})

@socketio.on("enter_union")
def on_enter_union(data):
    with client_lock:
        if client:
            client.enter_union(data.get("union_id", ""))

@socketio.on("approve")
def on_approve(data):
    with client_lock:
        if client:
            client.approve(int(data["uid"]))

@socketio.on("reject")
def on_reject(data):
    with client_lock:
        if client:
            client.reject(int(data["uid"]))

@socketio.on("toggle_auto")
def on_toggle_auto():
    with client_lock:
        if client:
            client.toggle_auto()

@socketio.on("toggle_debug")
def on_toggle_debug():
    with client_lock:
        if client:
            client.toggle_debug()

@socketio.on("refresh")
def on_refresh():
    with client_lock:
        if client:
            client.refresh_applicants()

@socketio.on("add_white")
def on_add_white(data):
    with client_lock:
        if client:
            client.add_white(int(data["uid"]))

@socketio.on("remove_white")
def on_remove_white(data):
    with client_lock:
        if client:
            client.remove_white(int(data["uid"]))

@socketio.on("add_black")
def on_add_black(data):
    with client_lock:
        if client:
            client.add_black(int(data["uid"]))

@socketio.on("remove_black")
def on_remove_black(data):
    with client_lock:
        if client:
            client.remove_black(int(data["uid"]))

@socketio.on("get_state")
def on_get_state():
    with client_lock:
        if client:
            client.push_state()


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
