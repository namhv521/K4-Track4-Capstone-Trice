"""Local recorder; raw video is an opt-in separate operation."""
import csv
import json
from pathlib import Path
FIELDS = ['session_id','event_id','episode_id','type','t_s','seat_id','person_id','object_id','reason']
def read_frames(log_path):
    with open(log_path, encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip(): yield json.loads(line)
class Recorder:
    def __init__(self, session_dir, manifest):
        self.root=Path(session_dir); self.root.mkdir(parents=True, exist_ok=False)
        self.session_id=manifest['session_id']; self.seen=set(); self.video=None; self.sidecar=None; self.index=0
        (self.root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        self.frames=(self.root/'frames.jsonl').open('w',encoding='utf-8')
        self.event_file=(self.root/'events.csv').open('w',newline='',encoding='utf-8')
        self.events=csv.DictWriter(self.event_file,fieldnames=FIELDS); self.events.writeheader()
    def write_frame(self, observation, decision, processing_ms):
        self.frames.write(json.dumps(dict(schema_version=1,session_id=self.session_id,observation=observation,decision=decision,processing_ms=processing_ms))+'\n')
        for event in decision.get('events',[]):
            key=(event['episode_id'],event['type'])
            if key not in self.seen:
                row=dict(event,session_id=self.session_id); self.events.writerow({k:row.get(k) for k in FIELDS}); self.seen.add(key)
        self.frames.flush(); self.event_file.flush()
    def write_video(self, frame, t_s):
        import cv2
        if self.video is None:
            h,w=frame.shape[:2]; self.video=cv2.VideoWriter(str(self.root/'raw.avi'),cv2.VideoWriter_fourcc(*'MJPG'),15,(w,h))
            if not self.video.isOpened(): raise RuntimeError('Video writer unavailable')
            self.sidecar=(self.root/'video_timestamps.csv').open('w',newline='',encoding='utf-8'); self.timestamps=csv.writer(self.sidecar); self.timestamps.writerow(['video_index','t_s'])
        self.video.write(frame); self.timestamps.writerow([self.index,t_s]); self.sidecar.flush(); self.index+=1
    def close(self):
        self.frames.close(); self.event_file.close()
        if self.video is not None: self.video.release()
        if self.sidecar is not None: self.sidecar.close()
