import unittest
from unittest.mock import patch
import cv2
import numpy as np
from fastapi.testclient import TestClient
from phone_security import PairingTokens
import web_backend as backend

class PhoneApiTests(unittest.TestCase):
    def test_disconnect_latest_reports_stopped_not_waiting(self):
        with TestClient(backend.app, client=('127.0.0.1', 1234)) as client:
            paired = client.post('/api/pair', json={}).json()
            with client.websocket_connect('/ws/' + paired['id']) as ws:
                ws.send_json({'type': 'auth', 'token': paired['token']})
                self.assertEqual(ws.receive_json()['type'], 'authenticated')
            result = client.get('/api/sessions/' + paired['id'] + '/latest').json()
            self.assertEqual(result['session_status'], 'stopped')
            self.assertTrue(result['stopped'])
            self.assertFalse(result['waiting_for_producer'])

    def test_qr_is_local_no_store_and_bounded(self):
        with TestClient(backend.app, client=('127.0.0.1', 1234)) as client:
            response = client.post('/api/qr', json={'text': 'https://demo.local/phone.html#session=demo&token=test'})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'<svg', response.content)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            self.assertEqual(client.post('/api/qr', json={'text': 'x'*2049}).status_code, 422)

    def test_motion_quality_reason_is_preserved(self):
        from types import SimpleNamespace
        config = backend.defaults()
        worker = backend.Worker('fake', config)
        worker.detector = SimpleNamespace(infer=lambda *args: {'tracks': [], 'quality_ok': True, 'quality_reasons': []})
        worker.motion = SimpleNamespace(update=lambda frame: {'stable': False, 'reason': 'insufficient_motion_features', 'score': 0.})
        worker.engine = SimpleNamespace(update=lambda observation: {'person_id': None, 'object_id': None, 'state': 'UNCERTAIN', 'events': []})
        with patch.object(backend, 'store'):
            result = worker.process(np.full((48,64,3),127,np.uint8), 0.)
        self.assertEqual(result['observation']['quality_reasons'], ['insufficient_motion_features'])

    def test_phone_frame_header_latest_and_seq_rejection(self):
        def fake_process(worker, frame, t_s):
            return {'session_id': worker.id, 'observation': {'t_s': t_s},
                    'decision': {'state': 'UNASSIGNED'}, 'frame': backend.encode(frame)}
        with TestClient(backend.app, client=('127.0.0.1', 1234)) as client, patch.object(backend.Worker, 'process', fake_process):
            pair = client.post('/api/pair', json={}).json()
            ok, jpeg = cv2.imencode('.jpg', np.full((48,64,3),127,np.uint8))
            with client.websocket_connect('/ws/' + pair['id']) as ws:
                ws.send_json({'type':'auth', 'token': pair['token']})
                self.assertEqual(ws.receive_json()['type'], 'authenticated')
                ws.send_json({'type':'frame', 'seq':1, 'capture_t_ms':1000.})
                ws.send_bytes(jpeg.tobytes())
                result = ws.receive_json()
                self.assertEqual(result['observation']['t_s'], 0.)
                self.assertEqual(client.get('/api/sessions/'+pair['id']+'/latest').json()['source']['seq'],1)
                ws.send_json({'type':'frame', 'seq':1, 'capture_t_ms':1100.})
                ws.send_bytes(jpeg.tobytes())
                self.assertEqual(ws.receive_json()['type'], 'error')

    def test_tokens_expire_are_scoped_and_revoked(self):
        clock = [0.]
        tokens = PairingTokens(ttl=10, clock=lambda: clock[0])
        token = tokens.issue('a')
        self.assertTrue(tokens.valid('a', token))
        self.assertFalse(tokens.valid('b', token))
        self.assertFalse(tokens.valid('a', 'wrong'))
        clock[0] = 11
        self.assertFalse(tokens.valid('a', token))
        tokens.revoke('a')
        self.assertNotIn('a', tokens.entries)

    def test_lan_cannot_read_desktop_api_or_create_pair(self):
        with TestClient(backend.app, client=('192.168.1.5', 1234)) as client:
            self.assertEqual(client.get('/api/sessions').status_code, 403)
            self.assertEqual(client.post('/api/pair', json={}).status_code, 403)

    def test_pair_authentication_and_observer(self):
        with TestClient(backend.app, client=('127.0.0.1', 1234)) as client:
            response = client.post('/api/pair', json={})
            self.assertEqual(response.status_code, 200)
            paired = response.json()
            self.assertIn('token=', paired['phone_fragment'])
            sid = paired['id']
            self.assertTrue(client.get(f'/api/sessions/{sid}/latest').json()['pending'])
            with client.websocket_connect(f'/ws/{sid}') as ws:
                ws.send_json({'type': 'auth', 'token': 'wrong'})
                self.assertEqual(ws.receive()['type'], 'websocket.close')
            self.assertFalse(backend.workers[sid].stopped)
            with client.websocket_connect(f'/ws/{sid}') as ws:
                ws.send_json({'type': 'auth', 'token': paired['token']})
                self.assertEqual(ws.receive_json()['type'], 'authenticated')
                ws.send_bytes(b'invalid')
                self.assertEqual(ws.receive_json()['type'], 'error')
            self.assertFalse(backend.tokens.valid(sid, paired['token']))
            ended = client.get(f'/api/sessions/{sid}/latest').json()
            self.assertEqual(ended['session_status'], 'error')
            self.assertTrue(ended['stopped'])
            self.assertFalse(ended['waiting_for_producer'])

if __name__ == '__main__': unittest.main()
