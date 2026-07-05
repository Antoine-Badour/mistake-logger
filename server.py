import json
import os
import re
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DB_PATH = os.path.join(os.path.dirname(__file__), "mistakes.db")
HTML_PATH = os.path.join(os.path.dirname(__file__), "mistake.html")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            website TEXT,
            unit TEXT,
            concept TEXT,
            note TEXT,
            details TEXT,
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_or_create_user(username):
    username = (username or "").strip()
    if not username:
        raise ValueError("Username is required")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()

    if row:
        user_id = row["id"]
    else:
        cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
        user_id = cur.lastrowid

    conn.commit()
    conn.close()
    return user_id


def get_user_mistakes(username):
    user_id = get_or_create_user(username)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, website, unit, concept, note, details, done
        FROM mistakes
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "website": row["website"] or "",
            "unit": row["unit"] or "",
            "concept": row["concept"] or "",
            "note": row["note"] or "",
            "details": row["details"] or "",
            "done": bool(row["done"]),
        }
        for row in rows
    ]


class MistakeHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.serve_file("mistake.html", "text/html; charset=utf-8")
            return

        if parsed.path == "/api/mistakes":
            username = parse_qs(parsed.query).get("username", [""])[0].strip()
            if not username:
                self.send_json(400, {"error": "Username is required"})
                return

            self.send_json(200, {"username": username, "mistakes": get_user_mistakes(username)})
            return

        self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/login":
            payload = self.read_json_body()
            username = (payload.get("username") or "").strip()
            if not username:
                self.send_json(400, {"error": "Username is required"})
                return

            get_or_create_user(username)
            self.send_json(200, {"username": username, "mistakes": get_user_mistakes(username)})
            return

        if parsed.path == "/api/mistakes":
            payload = self.read_json_body()
            username = (payload.get("username") or "").strip()
            if not username:
                self.send_json(400, {"error": "Username is required"})
                return

            user_id = get_or_create_user(username)
            website = payload.get("website") or ""
            unit = payload.get("unit") or ""
            concept = payload.get("concept") or ""
            note = payload.get("note") or ""
            details = payload.get("details") or ""
            done = 1 if payload.get("done") else 0

            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO mistakes (user_id, website, unit, concept, note, details, done, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, website, unit, concept, note, details, done, datetime.utcnow().isoformat()),
            )
            conn.commit()
            conn.close()

            self.send_json(201, {"username": username, "mistakes": get_user_mistakes(username)})
            return

        self.send_json(404, {"error": "Not found"})

    def do_PATCH(self):
        parsed = urlparse(self.path)
        match = re.fullmatch(r"/api/mistakes/(\d+)", parsed.path)
        if not match:
            self.send_json(404, {"error": "Not found"})
            return

        payload = self.read_json_body()
        username = (payload.get("username") or "").strip()
        id_value = int(match.group(1))

        if not username:
            self.send_json(400, {"error": "Username is required"})
            return

        user_id = get_or_create_user(username)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM mistakes WHERE id = ? AND user_id = ?", (id_value, user_id))
        row = cur.fetchone()

        if not row:
            conn.close()
            self.send_json(404, {"error": "Mistake not found"})
            return

        cur.execute("UPDATE mistakes SET done = ? WHERE id = ?", (1 if payload.get("done") else 0, id_value))
        conn.commit()
        conn.close()

        self.send_json(200, {"username": username, "mistakes": get_user_mistakes(username)})

    def do_DELETE(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/mistakes":
            username = parse_qs(parsed.query).get("username", [""])[0].strip()
            if not username:
                self.send_json(400, {"error": "Username is required"})
                return

            user_id = get_or_create_user(username)
            conn = get_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM mistakes WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            self.send_json(200, {"username": username, "mistakes": []})
            return

        match = re.fullmatch(r"/api/mistakes/(\d+)", parsed.path)
        if not match:
            self.send_json(404, {"error": "Not found"})
            return

        username = parse_qs(parsed.query).get("username", [""])[0].strip()
        if not username:
            self.send_json(400, {"error": "Username is required"})
            return

        user_id = get_or_create_user(username)
        id_value = int(match.group(1))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM mistakes WHERE id = ? AND user_id = ?", (id_value, user_id))
        conn.commit()
        conn.close()

        self.send_json(200, {"username": username, "mistakes": get_user_mistakes(username)})

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError:
            return {}

    def serve_file(self, filename, content_type):
        with open(os.path.join(os.path.dirname(__file__), filename), "r", encoding="utf-8") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    init_db()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), MistakeHandler)
    print(f"Mistake logger server running at http://{host}:{port}")
    server.serve_forever()
