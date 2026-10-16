import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import cv2
import numpy as np
from fastapi.testclient import TestClient
import web_backend as backend
from storage import Store

class FakeDetector:
    def __init__(self,*args): pass
    def infer(self,frame,frame_id,t_s):
        h,w=frame.shape[:2]
        return dict(frame_id=frame_id,t_s=t_s,width=w,height=h,quality_ok=True,quality_reasons=[],tracks=[],inference_ms=0)

class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir='runs')
        path=str(Path(self.temp.name)/'web.sqlite3')
        self.db=patch.object(backend,'Store',lambda *_:Store(path));self.db.start()
        self.detector=patch.object(backend,'Detector',FakeDetector);self.detector.start()
        backend.workers.clear()
        self.client=TestClient(backend.app, client=('127.0.0.1', 50000));self.client.__enter__()
    def tearDown(self):
        self.client.__exit__(None,None,None);self.detector.stop();self.db.stop();self.temp.cleanup()
    def test_catalog_and_invalid_video(self):
        videos=self.client.get('/api/videos').json();self.assertGreaterEqual(len(videos),3)
        self.assertEqual(self.client.post('/api/sessions',json={'video_id':'../../bad'}).status_code,404)
    def test_config_validation(self):
        for config in [{'confidence_min':-1},{'alert_after_exit_s':-1},{'processing_fps':2},{'roi_norm':[]}]:
            self.assertEqual(self.client.post('/api/sessions',json={'config':config}).status_code,422,config)
    def test_camera_socket_and_persistence(self):
        sid=self.client.post('/api/sessions',json={}).json()['id']
        _,image=cv2.imencode('.jpg',np.full((480,640,3),128,np.uint8))
        with self.client.websocket_connect('/ws/'+sid) as ws:
            ws.send_bytes(image.tobytes());row=ws.receive_json()
            self.assertEqual(row['session_id'],sid);self.assertEqual(row['observation']['width'],640)
        session=self.client.get('/api/sessions').json()[0]
        self.assertEqual(session['frame_count'],1)
        self.assertEqual(self.client.get('/api/sessions/'+sid+'/events').json(),[])
    def test_foreign_origin_rejected(self):
        from starlette.websockets import WebSocketDisconnect
        sid=self.client.post('/api/sessions',json={}).json()['id']
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect('/ws/'+sid,headers={'origin':'https://foreign.example'}): pass
        self.client.post('/api/sessions/'+sid+'/stop')
