from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, mimetypes, os, sqlite3, time

APP_NAME = "Reading Radar"
ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "app.db"

def db():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""create table if not exists records (
        id integer primary key autoincrement,
        title text not null,
        details text not null default '',
        status text not null default 'active',
        tag text not null default '',
        due_date text not null default '',
        created_at integer not null,
        updated_at integer not null
    )""")
    return con

def row(record):
    return dict(record)

class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        size = int(self.headers.get("content-length", "0"))
        return json.loads(self.rfile.read(size) or b"{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            return self.send_json({"ok": True, "app": APP_NAME})
        if path == "/api/records":
            with db() as con:
                records = con.execute("select * from records order by updated_at desc, id desc").fetchall()
            return self.send_json([row(record) for record in records])
        file_path = ROOT / "public" / ("index.html" if path == "/" else path.lstrip("/"))
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("content-type", mimetypes.guess_type(file_path)[0] or "text/plain")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlparse(self.path).path != "/api/records":
            self.send_error(404)
            return
        payload = self.read_json()
        now = int(time.time())
        with db() as con:
            cur = con.execute(
                "insert into records(title, details, status, tag, due_date, created_at, updated_at) values(?,?,?,?,?,?,?)",
                (payload.get("title", "").strip(), payload.get("details", "").strip(), payload.get("status", "active"), payload.get("tag", "").strip(), payload.get("due_date", ""), now, now),
            )
            record = con.execute("select * from records where id=?", (cur.lastrowid,)).fetchone()
        self.send_json(row(record), 201)

    def do_PUT(self):
        parts = urlparse(self.path).path.split("/")
        if len(parts) != 4 or parts[:3] != ["", "api", "records"]:
            self.send_error(404)
            return
        payload = self.read_json()
        now = int(time.time())
        with db() as con:
            con.execute(
                "update records set title=?, details=?, status=?, tag=?, due_date=?, updated_at=? where id=?",
                (payload.get("title", "").strip(), payload.get("details", "").strip(), payload.get("status", "active"), payload.get("tag", "").strip(), payload.get("due_date", ""), now, int(parts[3])),
            )
            record = con.execute("select * from records where id=?", (int(parts[3]),)).fetchone()
        self.send_json(row(record) if record else {}, 200 if record else 404)

    def do_DELETE(self):
        parts = urlparse(self.path).path.split("/")
        if len(parts) != 4 or parts[:3] != ["", "api", "records"]:
            self.send_error(404)
            return
        with db() as con:
            con.execute("delete from records where id=?", (int(parts[3]),))
        self.send_json({"ok": True})

print(f"{APP_NAME} on :{os.environ.get('PORT','3000')}")
ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "3000"))), Handler).serve_forever()
