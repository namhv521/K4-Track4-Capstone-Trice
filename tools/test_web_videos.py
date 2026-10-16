import asyncio,json,time
from pathlib import Path
import httpx,websockets
async def run():
    evidence=[]
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000',timeout=30) as client:
        videos=(await client.get('/api/videos')).json()
        for i,video in enumerate(videos):
            session=(await client.post('/api/sessions',json={'video_id':video['id']})).json()
            start=time.monotonic();n=0;tracks=0;states={};complete=False
            async with websockets.connect('ws://127.0.0.1:8000/ws/'+session['id'],max_size=8*1024*1024) as ws:
                while True:
                    message=json.loads(await asyncio.wait_for(ws.recv(),60))
                    if message.get('type')=='error':raise RuntimeError(message)
                    if message.get('type')=='complete':complete=True;break
                    n+=1;tracks+=len(message['observation']['tracks']);state=message['decision']['state'];states[state]=states.get(state,0)+1
                    if i>0 and n>=30:break
            await client.post('/api/sessions/'+session['id']+'/stop')
            summary=next(x for x in (await client.get('/api/sessions')).json() if x['id']==session['id'])
            result={'video':video['name'],'session_id':session['id'],'processed_frames_received':n,'complete':complete,'tracks_received':tracks,'states':states,'wall_s':round(time.monotonic()-start,2),'db_frame_count':summary['frame_count'],'accuracy_verified':False}
            evidence.append(result);print(json.dumps(result),flush=True)
            Path('evidence/web-video-test.json').write_text(json.dumps(evidence,indent=2))
asyncio.run(run())
