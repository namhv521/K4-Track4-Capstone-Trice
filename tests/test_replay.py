import json
from pathlib import Path
import tempfile
import unittest
from recorder import Recorder,read_frames
class RecorderTests(unittest.TestCase):
    def test_roundtrip_dedup(self):
        with tempfile.TemporaryDirectory(dir='runs') as root:
            path=Path(root)/'session'; w=Recorder(str(path),{'session_id':'test'})
            event=dict(event_id='e',episode_id=1,type='REMINDER',t_s=2,seat_id='A',person_id=1,object_id=7,reason='exit')
            for _ in range(2): w.write_frame({'t_s':2},{'events':[event]},10)
            w.close(); self.assertEqual(len(list(read_frames(path/'frames.jsonl'))),2)
            self.assertEqual(len((path/'events.csv').read_text().splitlines()),2)
    def test_existing_session_refused(self):
        with tempfile.TemporaryDirectory(dir='runs') as root:
            with self.assertRaises(FileExistsError): Recorder(root,{'session_id':'test'})
