"""COCO detections and measured ByteTrack tracks; no identity recognition."""
from pathlib import Path
import math
import os
from time import perf_counter


class Detector:
    def __init__(self, model_path: str, config: dict):
        self.model_path = model_path
        self.config = config
        self._model = None
        self._last_t = None

    def _load_model(self):
        if self._model is None:
            config_dir = Path(__file__).parent / 'runs' / 'ultralytics'
            config_dir.mkdir(parents=True, exist_ok=True)
            os.environ.setdefault('YOLO_CONFIG_DIR', str(config_dir))
            os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)
        return self._model

    def infer(self, frame_bgr, frame_id: int, t_s: float) -> dict:
        import numpy as np
        if not isinstance(frame_bgr, np.ndarray) or frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3 or frame_bgr.dtype != np.uint8:
            raise ValueError('frame_bgr must be a nonempty uint8 HxWx3 BGR image')
        height, width = frame_bgr.shape[:2]
        if not height or not width or not math.isfinite(t_s) or t_s < 0:
            raise ValueError('Invalid image dimensions or timestamp')
        if self._last_t is not None and t_s < self._last_t:
            raise ValueError('Timestamp moved backwards; reset detector for a new session')
        self._last_t = float(t_s)
        start = perf_counter()
        model = self._load_model()
        names = model.names
        requested = set(self.config.get('object_classes', ['backpack'])) | {'person'}
        class_ids = [int(i) for i, name in names.items() if name in requested]
        missing = requested - set(names.values())
        if missing:
            raise ValueError(f'Model classes missing: {sorted(missing)}')
        result = model.track(frame_bgr, persist=True, tracker='bytetrack.yaml', classes=class_ids,
                             conf=float(self.config.get('confidence_min', 0.35)),
                             imgsz=int(self.config.get('imgsz', 640)),
                             device=self.config.get('device', 'cpu'), verbose=False)[0]
        tracks = []
        boxes = result.boxes
        if boxes is not None:
            coords = boxes.xyxy.cpu().tolist()
            scores = boxes.conf.cpu().tolist()
            classes = boxes.cls.cpu().tolist()
            ids = boxes.id.cpu().tolist() if boxes.id is not None else [None] * len(coords)
            for xyxy, score, cls, track_id in zip(coords, scores, classes, ids):
                if not all(math.isfinite(float(v)) for v in [*xyxy, score]):
                    continue
                x1, y1, x2, y2 = xyxy
                box = [max(0., min(float(width), x1)), max(0., min(float(height), y1)),
                       max(0., min(float(width), x2)), max(0., min(float(height), y2))]
                if box[2] <= box[0] or box[3] <= box[1]:
                    continue
                # Only current model output is measured; never append lost/predicted tracks.
                tracks.append({'id': int(track_id) if track_id is not None else None,
                               'class_name': names[int(cls)], 'bbox_xyxy': box,
                               'confidence': float(score), 'observed': True})
        brightness = float(frame_bgr.mean())
        reasons = []
        if brightness < float(self.config.get('min_brightness', 15)):
            reasons.append('too_dark')
        if brightness > float(self.config.get('max_brightness', 245)):
            reasons.append('too_bright')
        return {'frame_id': int(frame_id), 't_s': float(t_s), 'width': width, 'height': height,
                'quality_ok': not reasons, 'quality_reasons': reasons, 'tracks': tracks,
                'inference_ms': (perf_counter() - start) * 1000,
                'perception': {'detector': 'Ultralytics YOLO COCO', 'tracker': 'ByteTrack',
                               'identity': 'temporary track ID; no face recognition',
                               'model_path': self.model_path, 'object_classes': sorted(requested - {'person'})}}

    def reset(self) -> None:
        self._last_t = None
        if self._model is not None:
            predictor = getattr(self._model, 'predictor', None)
            for tracker in getattr(predictor, 'trackers', []):
                tracker.reset()
            self._model.predictor = None
