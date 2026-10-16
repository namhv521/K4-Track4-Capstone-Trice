"""Localhost camera/video inference API. Images stay in RAM, SQLite stores metadata."""
import asyncio
import base64
from contextlib import asynccontextmanager
import hashlib
from io import BytesIO
import json
import math
import mimetypes
mimetypes.add_type("application/x-apple-aspen-config", ".mobileconfig")
from pathlib import Path
from time import monotonic, perf_counter
from urllib.parse import urlsplit

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from detector import Detector
from event_engine import EventEngine
from storage import Store
from phone_security import PairingTokens, is_loopback

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / 'models' / 'yolo11n.pt'
MAX_BYTES = 2 * 1024 * 1024
workers = {}
store = None
tokens = PairingTokens()
latest = {}


def video_catalog():
    result = []
    for path in sorted((ROOT / 'data').rglob('*')):
        relative = path.relative_to(ROOT)
        if path.is_file() and path.suffix.lower() in {'.avi', '.mp4', '.mov', '.mkv'} and not any(p.startswith('.') for p in relative.parts) and path.resolve().is_relative_to(ROOT / 'data'):
            result.append({'id': hashlib.sha256(str(relative).encode()).hexdigest()[:16],
                           'name': path.name, 'relative_path': relative.as_posix()})
    return result


class StartRequest(BaseModel):
    config: dict = Field(default_factory=dict)
    video_id: str | None = None


class QRRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2048)


class Worker:
    def __init__(self, session_id, config, video=None):
        self.id, self.config, self.video = session_id, config, video
        self.detector = Detector(str(MODEL), config)
        self.motion = None
        if config.get('mode') == 'classroom':
            from classroom_engine import ClassroomEngine
            from camera_quality import MotionGuard
            self.engine = ClassroomEngine(config)
            self.motion = MotionGuard(config)
        else:
            self.engine = EventEngine(config)
        self.lock = asyncio.Lock()
        self.stopped = False
        self.start = None
        self.frame_id = 0
        self.crops = {'person_crop': None, 'object_crop': None}
        self.socket = None
        self.paired = False
        self.source_start = None
        self.last_source_seq = None

    def process(self, frame, t_s):
        start = perf_counter()
        height, width = frame.shape[:2]
        if max(height, width) > 1280:
            scale = 1280 / max(height, width)
            frame = cv2.resize(frame, (round(width * scale), round(height * scale)))
        observation = self.detector.infer(frame, self.frame_id, t_s)
        if self.motion is not None:
            motion = self.motion.update(frame)
            observation['camera_motion'] = motion
            if not motion['stable']:
                observation['quality_ok'] = False
                observation['quality_reasons'].append(motion['reason'])
        decision = self.engine.update(observation)
        self.frame_id += 1
        for key, identity in [('person_crop', decision.get('person_id')), ('object_crop', decision.get('object_id'))]:
            for track in observation['tracks']:
                if identity is not None and track['id'] == identity and track['observed']:
                    x1, y1, x2, y2 = map(int, track['bbox_xyxy'])
                    crop = frame[y1:y2, x1:x2]
                    if crop.size:
                        scale = min(1., 180 / max(crop.shape[:2]))
                        self.crops[key] = encode(cv2.resize(crop, None, fx=scale, fy=scale))
        elapsed = (perf_counter() - start) * 1000
        store.record_frame(self.id, observation, decision, elapsed)
        output = {'observation': observation, 'decision': decision, 'processing_ms': elapsed,
                  'session_id': self.id, **self.crops}
        output['frame'] = encode(frame)
        return output


def encode(frame):
    ok, data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return base64.b64encode(data).decode('ascii') if ok else None


def stop_worker(worker, status='stopped'):
    worker.stopped = True
    worker.crops = {'person_crop': None, 'object_crop': None}
    tokens.revoke(worker.id)
    latest.pop(worker.id, None)
    return store.stop_session(worker.id, status=status)


def validate_config(config):
    for key in ('confidence_min', 'imgsz', 'stationary_s', 'association_s', 'leave_confirm_s',
                'alert_after_exit_s', 'max_frame_gap_s', 'stationary_radius_norm',
                'association_distance_norm', 'exit_hysteresis_norm', 'processing_fps'):
        value = config.get(key, 5 if key == 'processing_fps' else None)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            raise HTTPException(422, f'{key} must be a finite positive number')
    if not 3 <= config.get('processing_fps', 5) <= 10:
        raise HTTPException(422, 'processing_fps must be between 3 and 10')
    if not 0 < config['confidence_min'] <= 1 or not 160 <= config['imgsz'] <= 1280:
        raise HTTPException(422, 'Invalid confidence_min or imgsz')
    for key, minimum, maximum in [('roi_norm', 3, 12), ('exit_line_norm', 2, 2)]:
        points = config.get(key)
        if not isinstance(points, list) or not minimum <= len(points) <= maximum:
            raise HTTPException(422, f'Invalid {key}')
        for point in points:
            if not isinstance(point, list) or len(point) != 2 or any(not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in point):
                raise HTTPException(422, f'{key} coordinates must be normalized finite numbers')
    if config['exit_line_norm'][0] == config['exit_line_norm'][1]:
        raise HTTPException(422, 'Exit line cannot have zero length')
    if config.get('inside_side') not in {'left', 'right'}:
        raise HTTPException(422, 'inside_side must be left or right')


@asynccontextmanager
async def lifespan(app):
    global store
    store = Store(ROOT / 'data' / 'trice.sqlite3')
    yield
    for worker in list(workers.values()):
        stop_worker(worker)
    workers.clear()
    if hasattr(store, 'close'):
        store.close()


app = FastAPI(title='Trice Local Demo', lifespan=lifespan)


@app.post('/api/qr')
def pairing_qr(body: QRRequest):
    import qrcode
    from qrcode.image.svg import SvgPathImage
    image = qrcode.make(body.text, image_factory=SvgPathImage)
    buffer = BytesIO()
    image.save(buffer)
    return Response(buffer.getvalue(), media_type='image/svg+xml',
                    headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


@app.middleware('http')
async def private_desktop_api(request: Request, call_next):
    if request.url.path.startswith('/api/') and not is_loopback(request.client.host):
        return JSONResponse({'detail': 'Desktop API is available on loopback only'}, status_code=403)
    return await call_next(request)


@app.get('/api/status')
def status():
    return {'ok': True, 'model_ready': MODEL.is_file(), 'model': MODEL.name,
            'detector': 'YOLO11n COCO', 'tracker': 'ByteTrack',
            'active_sessions': sum(not w.stopped for w in workers.values()),
            'image_storage': False, 'mode': 'localhost'}


@app.get('/api/videos')
def videos():
    return video_catalog()


@app.get('/api/config')
def defaults():
    config = json.loads((ROOT / 'config.json').read_text(encoding='utf-8-sig'))
    config['processing_fps'] = 5
    return config


@app.post('/api/sessions')
@app.post('/api/video-sessions')
async def create_session(body: StartRequest):
    if not MODEL.is_file():
        raise HTTPException(503, 'Missing models/yolo11n.pt; install/download the local detector first')
    for session_id, pending in list(workers.items()):
        entry = tokens.entries.get(session_id)
        if pending.paired and pending.socket is None and (not entry or not tokens.valid(session_id, entry[0])):
            stop_worker(pending)
            workers.pop(session_id, None)
    if sum(not w.stopped for w in workers.values()) >= 2:
        raise HTTPException(409, 'Maximum two active sessions; stop a session first')
    config = json.loads((ROOT / 'config.json').read_text(encoding='utf-8-sig'))
    allowed = set(config) | {'object_classes', 'device', 'min_brightness', 'max_brightness', 'processing_fps',
                             'mode', 'tables', 'door_polygon_norm', 'camera_motion_threshold_norm'}
    if set(body.config) - allowed:
        raise HTTPException(422, 'Unknown config keys')
    config.update(body.config)
    validate_config(config)
    if config.get('mode') == 'classroom':
        from classroom_engine import validate_classroom_config
        try:
            validate_classroom_config(config)
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(422, str(exc)) from exc
    # Fixed model path; input config cannot select arbitrary server files.
    video = None
    if body.video_id:
        item = next((v for v in video_catalog() if v['id'] == body.video_id), None)
        if not item:
            raise HTTPException(404, 'Unknown video id')
        video = ROOT / item['relative_path']
    config['source'] = 'video:' + str(video.relative_to(ROOT)).replace('\\', '/') if video else 'browser:camera'
    summary = store.create_session(config)
    worker = Worker(summary['id'], config, video)
    workers[worker.id] = worker
    return {'id': worker.id, 'source': config['source'], 'config': config}


@app.post('/api/pair')
async def pair(body: StartRequest):
    if body.video_id:
        raise HTTPException(422, 'Pairing is for browser camera only')
    result = await create_session(body)
    worker = workers[result['id']]
    worker.paired = True
    token = tokens.issue(worker.id)
    return {**result, 'session_id': worker.id, 'token': token, 'expires_in_s': 600,
            'phone_fragment': f'#session={worker.id}&token={token}'}


@app.get('/api/sessions/{session_id}/latest')
def latest_frame(session_id: str):
    summary = store.get_session(session_id)
    if summary is None:
        raise HTTPException(404, 'Unknown session')
    worker = workers.get(session_id)
    if worker and worker.paired and worker.socket is None:
        entry = tokens.entries.get(session_id)
        if not entry or not tokens.valid(session_id, entry[0]):
            summary = stop_worker(worker)
            workers.pop(session_id, None)
    status = summary['status']
    pending = session_id not in latest
    return {**latest.get(session_id, {}), 'pending': pending, 'session_id': session_id,
            'session_status': status, 'stopped': status != 'running',
            'waiting_for_producer': status == 'running' and pending,
            'ended_at': summary.get('ended_at')}


@app.post('/api/sessions/{session_id}/stop')
async def stop(session_id: str):
    worker = workers.get(session_id)
    if worker:
        result = stop_worker(worker)
        if worker.socket:
            await worker.socket.close(code=1000)
        else:
            workers.pop(session_id, None)
            worker.detector._model = None
        return result
    result = store.stop_session(session_id)
    if result is None:
        raise HTTPException(404, 'Unknown session')
    return result


@app.get('/api/sessions')
def sessions():
    return store.list_sessions()


@app.get('/api/sessions/{session_id}/events')
def events(session_id: str):
    if store.get_session(session_id) is None:
        raise HTTPException(404, 'Unknown session')
    return store.list_events(session_id)


@app.websocket('/ws/{session_id}')
@app.websocket('/ws/video/{session_id}')
async def stream(socket: WebSocket, session_id: str):
    origin = socket.headers.get('origin')
    if origin:
        parsed = urlsplit(origin)
        if parsed.netloc != socket.headers.get('host'):
            await socket.close(code=1008, reason='Only same-origin browser is allowed')
            return
        if not is_loopback(socket.client.host) and parsed.scheme != 'https':
            await socket.close(code=1008, reason='Phone camera requires HTTPS')
            return
    worker = workers.get(session_id)
    if worker is None or worker.stopped:
        await socket.close(code=1008, reason='Session missing or stopped')
        return
    if not worker.paired and not is_loopback(socket.client.host):
        await socket.close(code=1008, reason='Unpaired producer requires loopback')
        return
    if worker.lock.locked():
        await socket.close(code=1008, reason='Session already connected')
        return
    await socket.accept()
    if worker.paired:
        try:
            auth = await asyncio.wait_for(socket.receive_json(), timeout=10)
            if auth.get('type') != 'auth' or not tokens.valid(session_id, auth.get('token')):
                await socket.close(code=1008, reason='Invalid or expired pairing')
                return
        except (ValueError, asyncio.TimeoutError, WebSocketDisconnect):
            await socket.close(code=1008, reason='Pairing authentication required')
            return
        # Another producer may have authenticated while this one awaited its first message.
        if worker.lock.locked():
            await socket.close(code=1008, reason='Session already connected')
            return
    cap = None
    end_status = 'stopped'
    async with worker.lock:
        worker.socket = socket
        try:
            if worker.paired:
                await socket.send_json({'type': 'authenticated', 'session_id': session_id})
            if worker.video:
                cap = cv2.VideoCapture(str(worker.video))
                if not cap.isOpened():
                    raise ValueError('Cannot open local video')
                fps = cap.get(cv2.CAP_PROP_FPS)
                if not np.isfinite(fps) or fps <= 0:
                    raise ValueError('Video has invalid FPS; timestamp cannot be established')
                stride = max(1, round(fps / worker.config.get('processing_fps', 5)))
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                index = 0
                # Media index/FPS defines event time, not playback speed or processed count.
                while not worker.stopped:
                    ok, frame = await asyncio.to_thread(cap.read)
                    if not ok:
                        end_status = 'completed'
                        await socket.send_json({'type': 'complete', 'session_id': session_id})
                        break
                    current = index
                    index += 1
                    if current % stride:
                        continue
                    result = await asyncio.to_thread(worker.process, frame, current / fps)
                    result['progress'] = {'frame_index': current, 'total_frames': total,
                                          'video_time_s': current / fps, 'duration_s': total / fps}
                    latest[session_id] = result
                    await socket.send_json(result)
                    await asyncio.sleep(min(stride / fps, .2))
            else:
                header = None
                while not worker.stopped:
                    message = await socket.receive()
                    if message['type'] == 'websocket.disconnect':
                        break
                    if message.get('text') is not None:
                        header = json.loads(message['text'])
                        if header.get('type') != 'frame' or header.get('source_clock', 'browser_monotonic') != 'browser_monotonic':
                            raise ValueError('Expected browser_monotonic frame header')
                        if not isinstance(header.get('seq'), int) or not isinstance(header.get('capture_t_ms'), (int, float)) or not math.isfinite(header['capture_t_ms']):
                            raise ValueError('Invalid source frame sequence or timestamp')
                        continue
                    payload = message.get('bytes')
                    if not payload or len(payload) > MAX_BYTES:
                        raise ValueError('Send binary JPEG frames of at most 2 MB')
                    # JPEG SOF dimensions are checked before allocating decoded image memory.
                    width, height = jpeg_dimensions(payload)
                    if not width or not height or max(width, height) > 2560:
                        raise ValueError('JPEG dimensions exceed 2560 pixels')
                    frame = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
                    if frame is None:
                        raise ValueError('Invalid JPEG')
                    received = monotonic()
                    if worker.start is None:
                        worker.start = received
                    if worker.paired and not tokens.valid(session_id, tokens.entries.get(session_id, (None,))[0]):
                        raise ValueError('Pairing expired')
                    t_s = received - worker.start
                    if header:
                        if worker.last_source_seq is not None and header['seq'] <= worker.last_source_seq:
                            raise ValueError('Source sequence must increase')
                        worker.last_source_seq = header['seq']
                        if worker.source_start is None:
                            worker.source_start = header['capture_t_ms']
                        t_s = (header['capture_t_ms'] - worker.source_start) / 1000
                    result = await asyncio.to_thread(worker.process, frame, t_s)
                    result['source'] = {'seq': header.get('seq') if header else None,
                                        'capture_t_ms': header.get('capture_t_ms') if header else None,
                                        'clock': 'browser_monotonic' if header else 'server_receive_monotonic',
                                        'latency_note': 'Processing time excludes network; browser/server clocks are not synchronized'}
                    header = None
                    if worker.paired:
                        tokens.touch(session_id)
                    latest[session_id] = result
                    await socket.send_json(result)
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            end_status = 'error'
            try:
                await socket.send_json({'type': 'error', 'error': str(exc)})
            except RuntimeError:
                pass
        finally:
            if cap is not None:
                cap.release()
            worker.socket = None
            stop_worker(worker, end_status)
            workers.pop(session_id, None)
            worker.detector._model = None
            try:
                await socket.close()
            except RuntimeError:
                pass


def jpeg_dimensions(data):
    if data[:2] != b'\xff\xd8':
        return 0, 0
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xff:
            return 0, 0
        marker = data[offset + 1]
        offset += 2
        if marker in (0xd8, 0xd9):
            continue
        length = int.from_bytes(data[offset:offset+2], 'big')
        if length < 2 or offset + length > len(data):
            return 0, 0
        if marker in (0xc0, 0xc1, 0xc2) and length >= 7:
            return int.from_bytes(data[offset+5:offset+7], 'big'), int.from_bytes(data[offset+3:offset+5], 'big')
        offset += length
    return 0, 0


if (ROOT / 'web').is_dir():
    app.mount('/', StaticFiles(directory=ROOT / 'web', html=True), name='web')
