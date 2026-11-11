#!/usr/bin/env python3
"""Local Hope Island web/API server with a shared SQLite store."""
from __future__ import annotations

import json
import mimetypes
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parent
WEB_ROOT = (ROOT / 'dist').resolve()
DATA_DIR = Path(os.environ.get('HOPE_DATA_DIR', ROOT / 'data')).resolve()
DB_PATH = DATA_DIR / 'hope-island.sqlite3'
ROLES = {'visitor', 'scarf', 'doctor', 'nurse', 'surgeon', 'scrub'}
STYLES = {'short', 'bob', 'scarf', 'cap', 'mask'}
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')


def connect():
    DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(DATA_DIR, 0o700)
    except OSError:
        pass
    db = sqlite3.connect(DB_PATH, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    return db


def initialize():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY, status TEXT NOT NULL DEFAULT 'open',
          created_at TEXT NOT NULL, expires_at TEXT
        );
        CREATE TABLE IF NOT EXISTS resident_profiles (
          id TEXT PRIMARY KEY, session_id TEXT REFERENCES sessions(id),
          status TEXT NOT NULL CHECK(status IN ('draft','joined')),
          display_name TEXT NOT NULL DEFAULT '', role TEXT NOT NULL,
          appearance_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS wishes (
          id TEXT PRIMARY KEY, resident_id TEXT REFERENCES resident_profiles(id),
          text TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'lit',
          created_at TEXT NOT NULL, completed_at TEXT
        );
        CREATE INDEX IF NOT EXISTS resident_profiles_status ON resident_profiles(status);
        CREATE INDEX IF NOT EXISTS wishes_resident ON wishes(resident_id);
        ''')
    try:
        os.chmod(DB_PATH, 0o600)
    except OSError:
        pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def validate_profile(body):
    if not isinstance(body, dict):
        raise ValueError('角色設定格式錯誤。')
    role = body.get('role')
    appearance = body.get('appearance')
    if role not in ROLES or not isinstance(appearance, dict):
        raise ValueError('請選擇有效的角色樣式。')
    style = appearance.get('style')
    if style not in STYLES:
        raise ValueError('請選擇有效的髮型或配件。')
    colors = {key: appearance.get(key) for key in ('shirt', 'pants', 'hair', 'skin')}
    if any(not isinstance(value, str) or not HEX.fullmatch(value) for value in colors.values()):
        raise ValueError('顏色格式錯誤。')
    name = body.get('displayName', '')
    if not isinstance(name, str) or len(name.strip()) > 18:
        raise ValueError('暱稱最多 18 個字。')
    return role, {**colors, 'style': style}, name.strip()


CONTENT = None

class Handler(BaseHTTPRequestHandler):
    server_version = 'HopeIsland/1.0'

    def log_message(self, fmt, *args):
        print('%s - %s' % (self.address_string(), fmt % args))

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        for key, value in getattr(self, 'extra_headers', {}).items(): self.send_header(key, value)
        self.extra_headers = {}
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length < 1 or length > 16_384:
            raise ValueError('資料長度不正確。')
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        if CONTENT and CONTENT.handle(self): return
        parsed = urlsplit(self.path)
        if parsed.path == '/api/health':
            self.send_json(200, {'ok': True, 'store': 'sqlite', 'sharedAcrossPages': True})
            return
        if parsed.path == '/api/profiles':
            status = parse_qs(parsed.query).get('status', ['draft'])[0]
            if status not in {'draft', 'joined'}:
                self.send_json(400, {'error': '狀態不正確。'})
                return
            with connect() as db:
                rows = db.execute('SELECT * FROM resident_profiles WHERE status=? ORDER BY updated_at DESC', (status,)).fetchall()
            self.send_json(200, {'profiles': [self.public_profile(row) for row in rows]})
            return
        if parsed.path.startswith('/api/profiles/'):
            profile_id = parsed.path.rsplit('/', 1)[-1]
            with connect() as db:
                row = db.execute('SELECT * FROM resident_profiles WHERE id=?', (profile_id,)).fetchone()
            if not row:
                self.send_json(404, {'error': '找不到這份角色設定。'})
            else:
                self.send_json(200, {'profile': self.public_profile(row)})
            return
        relative = unquote(parsed.path).lstrip('/') or 'taiwan-study.html'
        target = (WEB_ROOT / relative).resolve()
        if not target.is_relative_to(WEB_ROOT) or not target.is_file():
            self.send_error(404)
            return
        data = target.read_bytes()
        mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        if target.suffix in {'.js', '.html', '.css'}:
            mime = {'js': 'text/javascript', 'html': 'text/html', 'css': 'text/css'}[target.suffix[1:]]
        self.send_response(200)
        self.send_header('Content-Type', mime + ('; charset=utf-8' if mime.startswith(('text/', 'application/json')) else ''))
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def public_profile(row):
        return {'id': row['id'], 'status': row['status'], 'displayName': row['display_name'],
                'role': row['role'], 'appearance': json.loads(row['appearance_json']),
                'createdAt': row['created_at'], 'updatedAt': row['updated_at']}

    def do_POST(self):
        if CONTENT and CONTENT.handle(self): return
        if urlsplit(self.path).path != '/api/profiles':
            self.send_json(404, {'error': '找不到這項服務。'})
            return
        try:
            role, appearance, name = validate_profile(self.read_json())
            profile_id, timestamp = str(uuid.uuid4()), now()
            with connect() as db:
                db.execute('INSERT INTO resident_profiles(id,status,display_name,role,appearance_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',
                           (profile_id, 'draft', name, role, json.dumps(appearance), timestamp, timestamp))
                row = db.execute('SELECT * FROM resident_profiles WHERE id=?', (profile_id,)).fetchone()
            self.send_json(201, {'profile': self.public_profile(row)})
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json(400, {'error': str(error)})

    def do_PATCH(self):
        if CONTENT and CONTENT.handle(self): return
        profile_id = urlsplit(self.path).path.rsplit('/', 1)[-1]
        try:
            role, appearance, name = validate_profile(self.read_json())
            with connect() as db:
                cursor = db.execute("UPDATE resident_profiles SET role=?,appearance_json=?,display_name=?,updated_at=? WHERE id=? AND status='draft'",
                                    (role, json.dumps(appearance), name, now(), profile_id))
                row = db.execute('SELECT * FROM resident_profiles WHERE id=?', (profile_id,)).fetchone()
            if cursor.rowcount == 0:
                self.send_json(404, {'error': '找不到可編輯的草稿角色。'})
            else:
                self.send_json(200, {'profile': self.public_profile(row)})
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json(400, {'error': str(error)})

    def do_DELETE(self):
        if CONTENT and CONTENT.handle(self): return
        profile_id = urlsplit(self.path).path.rsplit('/', 1)[-1]
        with connect() as db:
            cursor = db.execute("DELETE FROM resident_profiles WHERE id=? AND status='draft'", (profile_id,))
        self.send_json(200 if cursor.rowcount else 404, {'deleted': bool(cursor.rowcount)})


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1', help='預設只接受本機連線；日後手機加入需由院內網路設定。')
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    initialize()
    global CONTENT
    from hope_content import ContentService
    CONTENT = ContentService(connect, DATA_DIR, ROOT / 'education-seed.json')
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f'希望島共用資料服務：http://{args.host}:{args.port}/')
    print(f'SQLite 資料庫：{DB_PATH}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服務已停止。')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
