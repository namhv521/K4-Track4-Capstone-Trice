import asyncio,json,ssl
from pathlib import Path
import cv2,httpx,websockets
async def run():
    tls=ssl.create_default_context(cafile='data/tls/trice-local-ca.crt')
    async with httpx.AsyncClient(base_url='https://localhost:8443',verify=tls,timeout=60) as client:
        cfg=(await client.get('/api/config')).json()
        cfg.update(mode='classroom',geometry_calibrated=True,tables=[{'id':'A01','name':'Bàn 01','polygon_norm':[[.1,.4],[.6,.4],[.6,.95],[.1,.95]]}],door_polygon_norm=[[.65,.15],[.95,.15],[.95,.95],[.65,.95]],exit_line_norm=[[.8,.15],[.8,.95]])
        r=await client.post('/api/pair',json={'config':cfg});r.raise_for_status();pair=r.json()
        cap=cv2.VideoCapture('data/local/video1.avi');ok,frame=cap.read();cap.release()
        assert ok
        _,jpg=cv2.imencode('.jpg',frame)
        results=[]
        async with websockets.connect('wss://localhost:8443/ws/'+pair['id'],ssl=tls,max_size=8*1024*1024) as ws:
            await ws.send(json.dumps({'type':'auth','token':pair['token']}))
            ack=json.loads(await ws.recv());assert ack['type']=='authenticated'
            for seq in range(3):
                await ws.send(json.dumps({'type':'frame','seq':seq,'capture_t_ms':seq*200,'source_clock':'browser_monotonic'}));await ws.send(jpg.tobytes())
                reply=json.loads(await asyncio.wait_for(ws.recv(),60))
                if reply.get('type')=='error':raise RuntimeError(reply)
                latest=(await client.get('/api/sessions/'+pair['id']+'/latest')).json()
                assert latest['observation']['frame_id']==reply['observation']['frame_id']
                results.append({'frame_id':reply['observation']['frame_id'],'state':reply['decision']['state'],'tables':len(reply['decision']['tables']),'source_seq':reply['source']['seq'],'image_received':bool(reply['frame'])})
        output={'kind':'TLS-verified simulated phone protocol with real local video image and real YOLO, not physical phone','session_id':pair['id'],'frames':results,'physical_phone_verified':False,'speaker_audibility_verified':False,'accuracy_verified':False}
        Path('evidence/phone-protocol-smoke.json').write_text(json.dumps(output,indent=2));print(json.dumps(output))
asyncio.run(run())
