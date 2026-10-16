import concurrent.futures
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from storage import Store, ROOT


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'evidence')
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'nested' / 'test.sqlite3'
        self.store = Store(str(self.path))

    def event(self, kind='REMINDER'):
        return dict(event_id='engine-event', episode_id='episode1', type=kind, t_s=1,
                    person_id=3, object_id=5, reason='observed crossing')

    def frame(self, sid, events=None):
        self.store.record_frame(sid, {'t_s': 1}, {'state': 'ATTENDED', 'events': events or []}, 4)

    def test_persistence_counters_and_dedup(self):
        session = self.store.create_session({'source': 'browser:camera', 'threshold': .6})
        sid = session['id']
        self.assertEqual(len(sid), 32)
        self.assertEqual(session['status'], 'running')
        self.frame(sid, [self.event(), self.event()])
        self.frame(sid, [self.event(), self.event('UNATTENDED_ALERT')])
        reopened = Store(str(self.path))
        session = reopened.get_session(sid)
        self.assertEqual((session['frame_count'], session['reminder_count'], session['alert_count']), (2, 1, 1))
        self.assertEqual(session['last_state'], 'ATTENDED')
        self.assertEqual(session['processing_total_ms'], 8)
        self.assertEqual(session['config']['source'], 'browser:camera')
        self.assertEqual(len(reopened.list_sessions()), 1)
        events = reopened.list_events(sid)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['person_id'], 3)
        self.assertEqual(events[0]['session_id'], sid)
        self.assertNotEqual(events[0]['id'], events[0]['event_id'])
        stopped = reopened.stop_session(sid)
        self.assertIsNotNone(stopped['ended_at'])
        self.assertEqual(stopped['status'], 'stopped')
        self.assertEqual(stopped['ended_at'], reopened.stop_session(sid)['ended_at'])
        with self.assertRaises(ValueError):
            self.frame(sid)

    def test_missing_session_and_path_boundary(self):
        self.assertIsNone(self.store.get_session('missing'))
        self.assertIsNone(self.store.stop_session('missing'))
        self.assertEqual(self.store.list_events('missing'), [])
        with self.assertRaises(ValueError):
            self.frame('missing')
        with self.assertRaises(ValueError):
            Store(str(ROOT.parent / 'outside.sqlite3'))
        with self.assertRaises(ValueError):
            self.store.list_sessions(-1)

    def test_invalid_event_does_not_partially_commit(self):
        sid = self.store.create_session({})['id']
        with self.assertRaises(ValueError):
            self.frame(sid, [self.event(), {**self.event(), 'type': 'OTHER'}])
        self.assertEqual(self.store.get_session(sid)['frame_count'], 0)
        self.assertEqual(self.store.list_events(sid), [])
        with self.assertRaises(ValueError):
            self.store.record_frame(sid, {}, {}, float('nan'))

    def test_parallel_frames_preserve_counters(self):
        sid = self.store.create_session({})['id']
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: self.frame(sid, [self.event()]), range(20)))
        session = self.store.get_session(sid)
        self.assertEqual(session['frame_count'], 20)
        self.assertEqual(session['reminder_count'], 1)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0], 'wal')
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(tables, {'sessions', 'events'})


if __name__ == '__main__':
    unittest.main()
