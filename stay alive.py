import threading
import time
import requests
import os

URL = os.environ.get("REPL_URL", "http://127.0.0.1:3000")
PING_INTERVAL = 15 # Replit 通常 50s~60s 會 sleep

# =========================
# HEALTH CHECK
# =========================
def is_alive():
    try:
        r = requests.get(URL, timeout=5)
        return r.status_code == 200
    except:
        return False


# =========================
# SELF PING LOOP
# =========================
def keep_alive_loop():
    while True:
        try:
            requests.get(URL)
            print("[KEEPALIVE] ping sent")
        except Exception as e:
            print("[KEEPALIVE ERROR]", e)

        time.sleep(PING_INTERVAL)


# =========================
# MONITOR LOOP
# =========================
def monitor():
    while True:
        if not is_alive():
            print("[WARN] app not responding")

            # Replit 無法真正 restart OS process
            # 所以只能 log + rely on external restart system
        time.sleep(10)


# =========================
# START
# =========================
def start():
    threading.Thread(target=keep_alive_loop, daemon=True).start()
    threading.Thread(target=monitor, daemon=True).start()

    print("[SYSTEM] keep-alive started")


if __name__ == "__main__":
    start()

    while True:
        time.sleep(999)
