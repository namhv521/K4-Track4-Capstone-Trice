"""Local SQLite summaries and events; never stores camera frames."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
import uuid

ROOT = Path(__file__).resolve().parent


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str = 'data/trice.sqlite3'):
        candidate = Path(path)
        self.path = (candidate if candidate.is_absolute() else ROOT / candidate).resolve()
        if not self.path.is_relative_to(ROOT):
            raise ValueError('Database must remain inside Trice')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, created_at TEXT NOT NULL, ended_at TEXT,
                    status TEXT NOT NULL, config_json TEXT NOT NULL,
                    frame_count INTEGER NOT NULL DEFAULT 0, last_state TEXT,
                    reminder_count INTEGER NOT NULL DEFAULT 0,
                    alert_count INTEGER NOT NULL DEFAULT 0,
                    processing_total_ms REAL NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
                    created_at TEXT NOT NULL, episode_id TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('REMINDER','UNATTENDED_ALERT')),
                    t_s REAL NOT NULL, details_json TEXT NOT NULL,
                    UNIQUE(session_id, episode_id, type)
                );
                CREATE INDEX IF NOT EXISTS event_session_idx ON events(session_id);
            ''')

    @contextmanager
    def _connection(self):
        # Each operation owns its connection, so callers can use different threads.
        db = sqlite3.connect(str(self.path), timeout=20)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _session(row):
        if row is None:
            return None
        result = dict(row)
        result['config'] = json.loads(result.pop('config_json'))
        return result

    def create_session(self, config: dict) -> dict:
        config_json = json.dumps(config, ensure_ascii=False, allow_nan=False)
        sid, created_at = uuid.uuid4().hex, utc_now()
        with self._connection() as db:
            db.execute('INSERT INTO sessions(id,created_at,status,config_json) VALUES(?,?,?,?)',
                       (sid, created_at, 'running', config_json))
            return self._session(db.execute('SELECT * FROM sessions WHERE id=?', (sid,)).fetchone())

    def get_session(self, id) -> dict | None:
        with self._connection() as db:
            return self._session(db.execute('SELECT * FROM sessions WHERE id=?', (id,)).fetchone())

    def list_sessions(self, limit=30) -> list:
        limit = self._limit(limit)
        with self._connection() as db:
            return [self._session(row) for row in db.execute('SELECT * FROM sessions ORDER BY created_at DESC,id DESC LIMIT ?', (limit,))]

    @staticmethod
    def _limit(limit):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise ValueError('limit must be a nonnegative integer')
        return limit

    def record_frame(self, session_id, observation, decision, processing_ms) -> None:
        processing_ms = float(processing_ms)
        if not math.isfinite(processing_ms) or processing_ms < 0:
            raise ValueError('processing_ms must be finite and nonnegative')
        events = []
        for event in decision.get('events', []):
            if event.get('type') not in ('REMINDER', 'UNATTENDED_ALERT') or not event.get('episode_id'):
                raise ValueError('Event requires supported type and episode_id')
            t_s = float(event['t_s'])
            if not math.isfinite(t_s) or t_s < 0:
                raise ValueError('Event timestamp must be finite and nonnegative')
            events.append((event, t_s, json.dumps(event, ensure_ascii=False, allow_nan=False)))
        with self._connection() as db:
            updated = db.execute('''UPDATE sessions SET frame_count=frame_count+1,
                last_state=?,processing_total_ms=processing_total_ms+? WHERE id=? AND status='running' ''',
                (decision.get('state'), processing_ms, session_id))
            if updated.rowcount != 1:
                raise ValueError('Session missing or no longer running')
            for event, t_s, details in events:
                inserted = db.execute('''INSERT INTO events(id,session_id,created_at,episode_id,type,t_s,details_json)
                    VALUES(?,?,?,?,?,?,?) ON CONFLICT(session_id,episode_id,type) DO NOTHING''',
                    (uuid.uuid4().hex, session_id, utc_now(), str(event['episode_id']), event['type'], t_s, details))
                if inserted.rowcount:
                    field = 'reminder_count' if event['type'] == 'REMINDER' else 'alert_count'
                    db.execute(f'UPDATE sessions SET {field}={field}+1 WHERE id=?', (session_id,))

    def stop_session(self, id, status='stopped') -> dict | None:
        if status not in ('stopped', 'completed', 'failed', 'error'):
            raise ValueError('Unsupported terminal status')
        with self._connection() as db:
            db.execute("UPDATE sessions SET ended_at=?,status=? WHERE id=? AND status='running'", (utc_now(), status, id))
            return self._session(db.execute('SELECT * FROM sessions WHERE id=?', (id,)).fetchone())

    def list_events(self, session_id=None, limit=100) -> list:
        limit = self._limit(limit)
        query, params = 'SELECT * FROM events', []
        if session_id is not None:
            query += ' WHERE session_id=?'
            params.append(session_id)
        query += ' ORDER BY created_at DESC,id DESC LIMIT ?'
        params.append(limit)
        with self._connection() as db:
            output = []
            for row in db.execute(query, params):
                stored = dict(row)
                event = json.loads(stored.pop('details_json'))
                # Stored DB identifiers take priority over any untrusted event keys.
                output.append({**event, **stored})
            return output
