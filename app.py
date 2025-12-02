import os
import hashlib
import sqlite3
from flask import Flask, request, send_file, redirect
from datetime import datetime
import io

app = Flask(__name__)

DB_FILE = "tracking.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id TEXT,
        recipient_hash TEXT,
        event_type TEXT,
        timestamp TEXT,
        user_agent TEXT,
        ip_hash TEXT
    );
    """)
    conn.commit()
    conn.close()

# -----------------------------
# HOME PAGE (Fixes your 404)
# -----------------------------
@app.route("/")
def home():
    return """
    <h1>Phishing Simulation Server</h1>
    <p>Status: <b>Running</b></p>
    <p>Available endpoints:</p>
    <ul>
        <li>/track/open/&lt;campaign&gt;/&lt;recipient&gt;.gif</li>
        <li>/track/click/&lt;campaign&gt;/&lt;recipient&gt;</li>
        <li>/landing.html</li>
        <li>/report</li>
    </ul>
    """

def log_event(campaign_id, recipient_hash, event_type):
    ua = request.headers.get('User-Agent', '')
    ip = request.remote_addr or "0.0.0.0"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO events (campaign_id, recipient_hash, event_type, timestamp, user_agent, ip_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (campaign_id, recipient_hash, event_type, datetime.utcnow(), ua, ip_hash))
    conn.commit()
    conn.close()

@app.route("/track/open/<campaign_id>/<recipient_hash>.gif")
def track_open(campaign_id, recipient_hash):
    log_event(campaign_id, recipient_hash, "open")

    # 1x1 pixel tracking gif
    gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    return send_file(io.BytesIO(gif), mimetype="image/gif")

@app.route("/track/click/<campaign_id>/<recipient_hash>")
def track_click(campaign_id, recipient_hash):
    log_event(campaign_id, recipient_hash, "click")
    return redirect("/landing.html")

@app.route("/landing.html")
def landing_page():
    return """
    <h1>Phishing Simulation Training</h1>
    <p>This was a <b>test phishing email</b>. Stay alert:</p>
    <ul>
    <li>Don’t click unknown links</li>
    <li>Check sender email address</li>
    <li>Don’t share passwords</li>
    <li>Report suspicious emails</li>
    </ul>
    """

@app.route("/report")
def report():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
    rows = cur.fetchall()
    conn.close()
    return dict(rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
