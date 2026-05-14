# Reversed Front (RF) Auto Door — Web UI

## Overview
A web-based UI for managing union member applications in the Komisureiya game. Replaces the original CLI script with a real-time browser interface.

## Architecture

### Backend
- **`app.py`** — Flask + Flask-SocketIO server (port 5000, threading mode)
- **`api_client.py`** — Adapted ApiClient class; emits real-time events via a callback instead of printing to stdout

### Frontend
- **`templates/index.html`** — Login page (email + password → WebSocket login)
- **`templates/dashboard.html`** — Main control dashboard
- **`static/style.css`** — Dark-theme CSS (no framework, pure CSS variables)

## Features
- **Login** — Authenticates against `https://api.komisureiya.com/api/users/log_in`
- **WebSocket** — Maintains persistent WS connection with heartbeat
- **Applicants panel** — Shows pending applicants; per-row Approve / Reject / → White / → Black buttons
- **White list** — Auto-approve: add/remove user IDs, persisted to `white.txt`
- **Black list** — Auto-reject: add/remove user IDs, persisted to `black.txt`
- **Auto mode** — Toggle: automatically processes queue based on white/black list
- **Debug mode** — Toggle: logs all raw WS send/recv messages
- **Activity log** — Live scrolling log of all events
- **Queue display** — Shows pending IDs waiting to be processed by auto worker

## Data Persistence
- `white.txt` — One user ID per line, auto-saved on changes
- `black.txt` — One user ID per line, auto-saved on changes

## Running
```
python app.py
```
Serves on port 5000. Workflow: `Start application`.

## Dependencies
- flask
- flask-socketio
- websocket-client
- requests
