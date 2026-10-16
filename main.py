"""Trice live/video dashboard and timestamp-preserving observation replay."""
import argparse
from collections import deque
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import time
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('YOLO_CONFIG_DIR',str(ROOT/'.ultralytics'))
from event_engine import EventEngine
from recorder import Recorder,read_frames

def local(value):
    path=Path(value).resolve()
    if not path.is_relative_to(ROOT): raise ValueError('Paths must stay inside Trice')
    return path

def dashboard(frame,obs,dec,cfg,mode,history,portraits,ms):
    import cv2
    import numpy as np
    h,w=frame.shape[:2]
    if w<640:
        factor=640/w; frame=cv2.resize(frame,(640,int(h*factor)))
        obs=dict(obs,width=640,height=frame.shape[0],tracks=[dict(tr,bbox_xyxy=[v*factor for v in tr['bbox_xyxy']]) for tr in obs.get('tracks',[])])
        h,w=frame.shape[:2]
    image=frame.copy()
    roi=np.array([[int(x*w),int(y*h)] for x,y in cfg['roi_norm']],np.int32)
    cv2.polylines(image,[roi],True,(170,170,170),1)
    p,q=[[int(x*w),int(y*h)] for x,y in cfg['exit_line_norm']]
    cv2.line(image,p,q,(0,210,250),2)
    cv2.putText(image,'EXIT / REMINDER LINE',(max(5,p[0]-170),max(22,p[1]+22)),cv2.FONT_HERSHEY_SIMPLEX,.48,(0,220,255),1)
    owner,bag=dec.get('person_id'),dec.get('object_id')
    for tr in obs.get('tracks',[]):
        x1,y1,x2,y2=map(int,tr['bbox_xyxy']); selected=tr['id'] is not None and tr['id'] in (owner,bag)
        color=(100,225,120) if selected else (200,180,110)
        cv2.rectangle(image,(x1,y1),(x2,y2),color,2 if selected else 1)
        label=f"{tr['class_name']} #{tr['id']} {tr['confidence']:.2f}"
        if tr['id']==owner and owner is not None: label='RELATED PERSON '+label
        cv2.putText(image,label,(x1,max(18,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.45,color,1)
        if mode not in ('SYNTHETIC','LOG REPLAY') and selected and tr.get('observed') and x2>x1 and y2>y1:
            crop=frame[max(0,y1):min(h,y2),max(0,x1):min(w,x2)]
            if crop.size: portraits['person' if tr['id']==owner else 'object']=crop.copy()
    panel=np.full((max(h,740),450,3),(26,29,34),np.uint8)
    def text(s,y,size=.48,color=(225,230,235)):
        cv2.putText(panel,str(s)[:59],(18,y),cv2.FONT_HERSHEY_SIMPLEX,size,color,1,cv2.LINE_AA)
    text('TRICE / SMART LIBRARY',35,.72)
    text(f'{mode} | Seat {cfg["seat_id"]} | {obs["t_s"]:.1f} s',65)
    tint=(90,100,255) if dec['state']=='ALERT' else (70,210,250) if dec['state']=='UNCERTAIN' else (120,225,145)
    text(dec['state'],107,.85,tint); text(dec.get('reason',''),136,.42)
    text(f'Related person #{owner} | Item #{bag}',171,.55)
    text('Temporary track - ownership NOT verified',195,.43)
    for name,x in [('person',18),('object',225)]:
        if name in portraits:
            crop=portraits[name]; scale=min(175/crop.shape[1],140/crop.shape[0]); thumb=cv2.resize(crop,None,fx=scale,fy=scale)
            panel[212:212+thumb.shape[0],x:x+thumb.shape[1]]=thumb
    text('Last observed related person / item',374,.43)
    text('HOW THE PERSON IS ASSOCIATED',411,.53)
    text('YOLO detection + ByteTrack temporary IDs',438,.44)
    text('2D proximity + stable item + time + exit',463,.44)
    duration=dec.get('association_duration_s',0); distance=dec.get('association_distance_norm')
    text(f'Evidence: near for {duration:.1f}s | distance '+(f'{distance:.3f}' if distance is not None else '--'),488,.43)
    text(f'Linked: {dec.get("associated")} | Stationary: {dec.get("stationary")}',513,.45)
    remaining=dec.get('remaining_s'); text(f'Alert wait: {remaining:.1f}s' if remaining is not None else 'Alert wait: --',540)
    text(f'Inference {obs.get("inference_ms",0):.0f}ms | pipeline {ms:.0f}ms',566,.43)
    if not cfg.get('geometry_calibrated'): text('GEOMETRY DEFAULT - press C to configure',592,.42,(70,210,250))
    for i,msg in enumerate(history): text(msg,620+i*22,.4,(145,220,245))
    text('Q quit | R reset | S record | C configure',720,.43)
    result=np.full((panel.shape[0],w+450,3),(18,20,24),np.uint8); result[:h,:w]=image; result[:,w:]=panel
    return result

def calibrate(frame,cfg,path):
    import cv2
    x,y,w,h=cv2.selectROI('Select seat area / ENTER confirm',frame,False,False); cv2.destroyWindow('Select seat area / ENTER confirm')
    if not w or not h: return
    height,width=frame.shape[:2]
    cfg['roi_norm']=[[x/width,y/height],[(x+w)/width,y/height],[(x+w)/width,(y+h)/height],[x/width,(y+h)/height]]
    cfg['exit_line_norm']=[[(x+w)/width,0],[(x+w)/width,1]]; cfg['inside_side']='left'; cfg['geometry_calibrated']=True
    path.write_text(json.dumps(cfg,indent=2),encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__); group=parser.add_mutually_exclusive_group()
    group.add_argument('--source',default=None); group.add_argument('--fixture'); group.add_argument('--replay')
    parser.add_argument('--config',default=str(ROOT/'config.json')); parser.add_argument('--model',default=str(ROOT/'models/yolo11n.pt'))
    for flag in ['headless','record','record-video','calibrate','sound']: parser.add_argument('--'+flag,action='store_true')
    parser.add_argument('--max-frames',type=int,default=0); parser.add_argument('--snapshot')
    args=parser.parse_args(); path=local(args.config); cfg=json.loads(path.read_text(encoding='utf-8-sig')); engine=EventEngine(cfg)
    source=args.source if args.source is not None else '0'; mode='SYNTHETIC' if args.fixture else 'LOG REPLAY' if args.replay else 'LIVE' if source.isdigit() else 'VIDEO'
    cap=None; detector=None; recorder=None; history=deque(maxlen=3); portraits={}; final=None; count=0; decision={}
    def recording():
        session=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        model=local(args.model)
        manifest=dict(session_id=session,schema_version=1,source=source,mode=mode,config=cfg,config_sha256=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),model=str(model),model_sha256=hashlib.sha256(model.read_bytes()).hexdigest() if model.exists() else None,timestamp_basis='saved source' if args.fixture or args.replay else 'monotonic app receive' if mode=='LIVE' else 'frame index/media FPS',raw_media_opt_in=args.record_video,identity='temporary ID; ownership unverified')
        return Recorder(str(ROOT/'runs'/session),manifest)
    try:
        if (args.record or args.record_video) and not args.calibrate: recorder=recording()
        if args.fixture or args.replay: stream=read_frames(str(local(args.fixture or args.replay)))
        else:
            import cv2
            from detector import Detector
            cap=cv2.VideoCapture(int(source) if source.isdigit() else str(local(source)))
            if not cap.isOpened(): raise RuntimeError('Camera/video unavailable: check permissions and --source')
            detector=Detector(str(local(args.model)),cfg); stream=None
        start=time.monotonic()
        while True:
            tick=time.perf_counter()
            if stream is not None:
                try: row=next(stream)
                except StopIteration: break
                obs=row.get('observation',row); frame=None
            else:
                ok,frame=cap.read()
                if not ok:
                    if mode=='LIVE': raise RuntimeError('Camera stopped: session stopped, timers do not advance blindly')
                    break
                if count==0 and args.calibrate:
                    if args.headless: raise ValueError('Calibration needs display')
                    calibrate(frame,cfg,path); engine=EventEngine(cfg)
                    if args.record or args.record_video: recorder=recording()
                fps=cap.get(5); t=time.monotonic()-start if mode=='LIVE' else count/(fps if fps>0 else 25)
                obs=detector.infer(frame,count,t)
            decision=engine.update(obs); ms=(time.perf_counter()-tick)*1000
            for event in decision.get('events',[]):
                history.append(f"{event['type']} person #{event['person_id']} item #{event['object_id']}"); print(json.dumps(event),flush=True)
                if args.sound and mode=='LIVE':
                    try:
                        import winsound
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    except (ImportError,RuntimeError): pass
            if recorder:
                recorder.write_frame(obs,decision,ms)
                if args.record_video and frame is not None: recorder.write_video(frame,obs['t_s'])
            if not args.headless or args.snapshot:
                import cv2
                if frame is None:
                    import numpy as np
                    frame=np.full((obs['height'],obs['width'],3),35,np.uint8); cv2.putText(frame,mode+' / NO RAW IMAGE',(15,35),cv2.FONT_HERSHEY_SIMPLEX,.6,(230,230,230),1)
                final=dashboard(frame,obs,decision,cfg,mode,history,portraits,ms)
                if not args.headless:
                    cv2.imshow('Trice - related person and evidence',final); key=cv2.waitKey(1 if mode=='LIVE' else 25)&255
                    if key==ord('q'): break
                    if key==ord('r'):
                        engine.reset(); portraits.clear(); history.append('MANUAL RESET')
                        if recorder: recorder.close(); recorder=None
                        if detector: detector.reset()
                    if key==ord('c') and mode=='LIVE':
                        if recorder: recorder.close(); recorder=None
                        calibrate(frame,cfg,path); engine=EventEngine(cfg); portraits.clear(); detector.reset(); history.append('GEOMETRY RESET - press S to record')
                    if key==ord('s'):
                        if recorder: recorder.close(); recorder=None
                        else: recorder=recording()
            count+=1
            if args.max_frames and count>=args.max_frames: break
        if args.snapshot and final is not None:
            import cv2
            out=local(args.snapshot); out.parent.mkdir(parents=True,exist_ok=True); cv2.imwrite(str(out),final)
        print(json.dumps(dict(mode=mode,frames=count,state=decision.get('state'),live_accuracy_verified=False)))
    finally:
        if cap is not None: cap.release()
        if recorder: recorder.close()
        if not args.headless:
            import cv2
            cv2.destroyAllWindows()
if __name__=='__main__': main()
