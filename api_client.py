import requests
import websocket
import json
import threading
import time
import os
import sys

BASE_URL = "https://api.komisureiya.com/api"

folder = os.path.dirname(os.path.abspath(__file__))
WHITE_FILE = os.path.join(folder, "white.txt")
BLACK_FILE = os.path.join(folder, "black.txt")


class ApiClient:
    def __init__(self, email, password, emit_fn=None):
        self.session = requests.Session()
        self.email = email
        self.password = password

        self.user_id = None
        self.user_token = None

        self.ws = None
        self.running = False
        self.msg_id = 100

        self.union_id = None
        self.applied = set()
        self.queue = []

        self.white_list = set()
        self.black_list = set()

        self.load_lists()

        self.auto_door = False
        self.debug = False

        self.emit = emit_fn or (lambda event, data: None)
        self.log_buffer = []

    def log(self, message):
        self.log_buffer.append(message)
        if len(self.log_buffer) > 100:
            self.log_buffer = self.log_buffer[-100:]
        self.emit("log", {"message": message})

    def push_state(self):
        self.emit("state", {
            "connected": self.ws is not None and self.running,
            "user_id": self.user_id,
            "union_id": self.union_id,
            "auto": self.auto_door,
            "debug": self.debug,
            "applied": sorted(self.applied),
            "queue": list(self.queue),
            "white_list": sorted(self.white_list),
            "black_list": sorted(self.black_list),
        })

    # =====================================================
    # FILE SYSTEM
    # =====================================================
    def load_lists(self):
        if not os.path.exists(WHITE_FILE):
            open(WHITE_FILE, "w", encoding="utf-8").close()
        if not os.path.exists(BLACK_FILE):
            open(BLACK_FILE, "w", encoding="utf-8").close()

        with open(WHITE_FILE, "r", encoding="utf-8") as f:
            self.white_list = {int(l.strip()) for l in f if l.strip().isdigit()}
        with open(BLACK_FILE, "r", encoding="utf-8") as f:
            self.black_list = {int(l.strip()) for l in f if l.strip().isdigit()}

    def save_white(self):
        with open(WHITE_FILE, "w", encoding="utf-8") as f:
            for uid in sorted(self.white_list):
                f.write(str(uid) + "\n")

    def save_black(self):
        with open(BLACK_FILE, "w", encoding="utf-8") as f:
            for uid in sorted(self.black_list):
                f.write(str(uid) + "\n")

    # =====================================================
    # LOGIN
    # =====================================================
    def login(self):
        res = self.session.post(
            f"{BASE_URL}/users/log_in",
            data={
                "user[email]": self.email,
                "user[password]": self.password,
                "locale": "zh_TW",
                "app_version": "2.28",
                "key": "t9cTpsbSCYcJgsrrC"
            },
            headers={"User-Agent": "Mozilla/5.0"}
        )

        data = res.json()
        if data.get("status") != "ok":
            raise Exception(str(data))

        self.user_id = data["data"]["user_id"]
        self.user_token = data["data"]["user_token"]
        self.log(f"Login OK: user_id={self.user_id}")

    # =====================================================
    # WS
    # =====================================================
    def connect_ws(self):
        url = (
            f"wss://api.komisureiya.com/socket/websocket"
            f"?userToken={self.user_token}"
            f"&locale=zh_TW&vsn=2.0.0"
        )
        self.ws = websocket.create_connection(url)
        self.running = True
        self.log("WebSocket connected")

    def send(self, packet):
        self.ws.send(json.dumps(packet))
        if self.debug:
            self.log(f"SEND: {packet}")

    def next_id(self):
        self.msg_id += 1
        return str(self.msg_id)

    # =====================================================
    # LIST CONTROL
    # =====================================================
    def add_white(self, uid):
        uid = int(uid)
        self.white_list.add(uid)
        self.black_list.discard(uid)
        self.save_white()
        self.save_black()
        self.log(f"White list add: {uid}")
        self.push_state()

    def remove_white(self, uid):
        uid = int(uid)
        self.white_list.discard(uid)
        self.save_white()
        self.log(f"White list remove: {uid}")
        self.push_state()

    def add_black(self, uid):
        uid = int(uid)
        self.black_list.add(uid)
        self.white_list.discard(uid)
        self.save_black()
        self.save_white()
        self.log(f"Black list add: {uid}")
        self.push_state()

    def remove_black(self, uid):
        uid = int(uid)
        self.black_list.discard(uid)
        self.save_black()
        self.log(f"Black list remove: {uid}")
        self.push_state()

    # =====================================================
    # QUEUE
    # =====================================================
    def enqueue(self, uid):
        if uid not in self.queue:
            self.queue.append(uid)

    # =====================================================
    # AUTO WORKER
    # =====================================================
    def auto_worker(self):
        while self.running:
            if not self.auto_door:
                time.sleep(1)
                continue
            if not self.queue:
                time.sleep(1)
                continue

            uid = self.queue.pop(0)
            try:
                if uid in self.white_list:
                    self.approve(uid)
                elif uid in self.black_list:
                    self.reject(uid)
            except Exception as e:
                self.log(f"Auto error: {e}")

            time.sleep(1)

    # =====================================================
    # POLL APPLICANTS
    # =====================================================
    def poll_union(self):
        while self.running:
            if self.union_id:
                self.send([
                    "26", self.next_id(),
                    f"union:{self.union_id}",
                    "union_applicants", {}
                ])
            time.sleep(3600)

    # =====================================================
    # ACTIONS
    # =====================================================
    def approve(self, uid):
        uid = int(uid)
        self.send([
            "26", self.next_id(),
            f"union:{self.union_id}",
            "approve_member",
            {"user_id": uid}
        ])
        self.applied.discard(uid)
        if uid in self.queue:
            self.queue.remove(uid)
        self.log(f"Approved: {uid}")
        self.push_state()

    def reject(self, uid):
        uid = int(uid)
        self.send([
            "26", self.next_id(),
            f"union:{self.union_id}",
            "reject_member",
            {"user_id": uid}
        ])
        self.applied.discard(uid)
        if uid in self.queue:
            self.queue.remove(uid)
        self.log(f"Rejected: {uid}")
        self.push_state()

    # =====================================================
    # MESSAGE HANDLER
    # =====================================================
    def handle_message(self, raw):
        try:
            msg = json.loads(raw)
        except:
            return

        if self.debug:
            self.log(f"RECV: {msg}")

        if not isinstance(msg, list) or len(msg) < 5:
            return

        topic = msg[2]
        event = msg[3]
        payload = msg[4]

        if (
            topic == f"player:{self.user_id}"
            and event == "update_data"
            and "union_applicants" in payload
        ):
            applicants = payload["union_applicants"]
            new_ids = {x["id"] for x in applicants if x.get("id")}
            new = new_ids - self.applied
            self.applied.update(new_ids)

            if new:
                self.log(f"New applicants: {sorted(new)}")

            for uid in new_ids:
                self.enqueue(uid)

            self.push_state()
            return

        if isinstance(topic, str) and topic.startswith("union:"):
            if event == "phx_reply":
                response = payload.get("response", {})
                applicants = response.get("union_applicants")
                if applicants is not None:
                    new_ids = {x["id"] for x in applicants if x.get("id")}
                    self.applied = new_ids
                    self.log(f"Applied refreshed: {sorted(self.applied)}")
                    for uid in new_ids:
                        self.enqueue(uid)
                    self.push_state()

    # =====================================================
    # THREADS
    # =====================================================
    def receiver(self):
        while self.running:
            try:
                msg = self.ws.recv()
                self.handle_message(msg)
            except Exception as e:
                self.log(f"Receiver stopped: {e}")
                self.running = False
                self.emit("disconnected", {})
                break

    def heartbeat_loop(self):
        while self.running:
            try:
                self.send([None, self.next_id(), "phoenix", "heartbeat", {}])
            except:
                break
            time.sleep(30)

    def start(self):
        threading.Thread(target=self.receiver, daemon=True).start()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.auto_worker, daemon=True).start()
        threading.Thread(target=self.poll_union, daemon=True).start()
        self.log("All threads started")

    # =====================================================
    # CORE
    # =====================================================
    def join_core(self):
        self.send(["6", "6", f"player:{self.user_id}", "phx_join", {}])
        self.send(["9", "9", "all_players", "phx_join", {}])
        self.send(["12", "12", "locale:zh_TW", "phx_join", {}])
        self.log("Core channels joined")

    # =====================================================
    # UNION
    # =====================================================
    def enter_union(self, union_id):
        self.union_id = str(union_id)
        self.send(["26", self.next_id(), f"union:{union_id}", "phx_join", {}])
        time.sleep(0.5)
        self.send(["26", self.next_id(), f"union:{union_id}", "union_applicants", {}])
        self.log(f"Entered union: {union_id}")
        self.push_state()

    def toggle_auto(self):
        self.auto_door = not self.auto_door
        self.log(f"Auto mode: {'ON' if self.auto_door else 'OFF'}")
        self.push_state()

    def toggle_debug(self):
        self.debug = not self.debug
        self.log(f"Debug mode: {'ON' if self.debug else 'OFF'}")
        self.push_state()

    def refresh_applicants(self):
        if self.union_id:
            self.send([
                "26", self.next_id(),
                f"union:{self.union_id}",
                "union_applicants", {}
            ])
            self.log("Applicants refresh requested")
