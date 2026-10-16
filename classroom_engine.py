"""Conservative per-table evidence and finite doorway crossing, no identity claims."""
from copy import deepcopy
from math import hypot, isfinite
from event_engine import EventEngine


def inside(point, polygon):
    x,y=point; result=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result


def intersection(a,b,c,d):
    rx,ry=b[0]-a[0],b[1]-a[1];sx,sy=d[0]-c[0],d[1]-c[1]
    cross=rx*sy-ry*sx
    if abs(cross)<1e-10:return None
    qx,qy=c[0]-a[0],c[1]-a[1]
    t=(qx*sy-qy*sx)/cross;u=(qx*ry-qy*rx)/cross
    return (a[0]+t*rx,a[1]+t*ry) if 0<=t<=1 and 0<=u<=1 else None


def validate_classroom_config(config):
    def polygon(value,name):
        if not isinstance(value,list) or len(value)<3:raise ValueError(name+' needs at least 3 points')
        for p in value:
            if not isinstance(p,(list,tuple)) or len(p)!=2 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not isfinite(x) or not 0<=x<=1 for x in p):raise ValueError(name+' requires finite normalized points')
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(value,value[1:]+value[:1]))
        if abs(area)<1e-6:raise ValueError(name+' has no area')
    tables=config.get('tables')
    if not isinstance(tables,list) or not tables:raise ValueError('Configure at least one table')
    ids=set()
    for table in tables:
        if not isinstance(table,dict) or not isinstance(table.get('id'),str) or not table['id'] or table['id'] in ids:raise ValueError('Table IDs must be unique nonempty strings')
        ids.add(table['id']);polygon(table.get('polygon_norm'),'table '+table['id'])
    polygon(config.get('door_polygon_norm'),'door_polygon_norm')
    line=config.get('exit_line_norm')
    if not isinstance(line,list) or len(line)!=2:raise ValueError('Exit line needs two points')
    for p in line:
        if not isinstance(p,(list,tuple)) or len(p)!=2 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not isfinite(x) or not 0<=x<=1 for x in p):raise ValueError('Invalid exit line')
    if line[0]==line[1]:raise ValueError('Exit line needs distinct points')
    if config.get('inside_side','left') not in ('left','right'):raise ValueError('inside_side must be left or right')


class ClassroomEngine:
    def __init__(self,config):
        validate_classroom_config(config)
        self.config=deepcopy(config);self.camera_moved=False;self.generation=0
        self.reset()

    def reset(self):
        # Reset is not recalibration: camera movement requires a new session/config.
        self.generation+=1;self.previous={};self.last_t=None;self.engines={}
        for table in self.config['tables']:
            c=dict(self.config,roi_norm=table['polygon_norm'],seat_id=table['id'])
            self.engines[table['id']]=EventEngine(c)

    def _point(self,tr,obs,person=False):
        x1,y1,x2,y2=tr['bbox_xyxy'];return ((x1+x2)/2/obs['width'],(y2 if person else (y1+y2)/2)/obs['height'])

    def update(self,observation):
        t=float(observation['t_s'])
        if not isfinite(t) or t<0 or self.last_t is not None and t<self.last_t:raise ValueError('invalid or backwards timestamp')
        gap=self.last_t is not None and t-self.last_t>self.config['max_frame_gap_s'];self.last_t=t
        if 'camera_moved' in observation.get('quality_reasons',[]):self.camera_moved=True
        blocked=self.camera_moved or not self.config.get('geometry_calibrated',False)
        valid=observation.get('quality_ok',False) and not blocked and not gap
        if not valid:self.previous={}
        tracks=[tr for tr in observation.get('tracks',[]) if tr.get('observed') is True and tr.get('id') is not None and tr.get('confidence',0)>=self.config['confidence_min']]
        people={tr['id']:tr for tr in tracks if tr['class_name']=='person'}
        classes=self.config.get('object_classes',['backpack','handbag','suitcase'])
        table_bags={};bag_tables={}
        for table in self.config['tables']:
            bags=[tr for tr in tracks if tr['class_name'] in classes and inside(self._point(tr,observation),table['polygon_norm'])]
            table_bags[table['id']]=bags
            for tr in bags:bag_tables.setdefault(tr['id'],[]).append(table['id'])
        nearby={}
        for tid,bags in table_bags.items():
            if len(bags)!=1 or len(bag_tables[bags[0]['id']])!=1:continue
            bp=self._point(bags[0],observation)
            for pid,tr in people.items():
                pp=self._point(tr,observation,True)
                if hypot(pp[0]-bp[0],pp[1]-bp[1])<=self.config['association_distance_norm']:nearby.setdefault(pid,[]).append(tid)
        assignments={e.person_id:tid for tid,e in self.engines.items() if e.person_id is not None}
        object_assignments={e.object_id:tid for tid,e in self.engines.items() if e.object_id is not None}
        decisions=[];events=[]
        for table in self.config['tables']:
            tid=table['id'];engine=self.engines[tid];bags=table_bags[tid]
            selected=[tr for tr in bags if len(bag_tables[tr['id']])==1 and object_assignments.get(tr['id'],tid)==tid]
            allowed=[]
            for pid,tr in people.items():
                if engine.person_id==pid:allowed.append(tr)
                elif engine.person_id is None and pid not in assignments and len(nearby.get(pid,[]))==1:allowed.append(tr)
            owner=people.get(engine.person_id);crossing_ok=False
            if owner and valid:
                point=self._point(owner,observation,True);previous=self.previous.get(owner['id'])
                if previous:
                    hit=intersection(previous,point,*self.config['exit_line_norm'])
                    crossing_ok=hit is not None and inside(hit,self.config['door_polygon_norm'])
                if engine.t_exit is None and engine._side(point)=='outside' and engine.last_side=='inside' and not crossing_ok:engine.last_side=None
            filtered=dict(observation,tracks=allowed+selected,quality_ok=valid)
            d=engine.update(filtered)
            if blocked:
                d['state']='UNCERTAIN';d['reason']='CAMERA_MOVED_RECALIBRATION_REQUIRED' if self.camera_moved else 'CLASSROOM_GEOMETRY_NOT_CONFIGURED'
            if d['reason']=='OWNER_OUTSIDE_WITHOUT_CONTINUOUS_CROSSING':d['reason']='NO_VERIFIED_DOORWAY_CROSSING'
            d['table_id']=tid;d['table_name']=table.get('name',tid)
            d['episode_id']=f'{self.generation}:{tid}:{engine.episode}' if engine.t_exit is not None else None
            for event in d['events']:
                event['episode_id']=f'{self.generation}:{tid}:{event["episode_id"]}'
                event['event_id']=f'{self.config.get("session_id","session")}:{event["episode_id"]}:{event["type"]}'
                event['table_name']=d['table_name']
                event['room_exit_confirmed']=True
                event['announcement_text']=f'Xin kiểm tra đồ còn lại tại {d["table_name"]}.' if event['type']=='REMINDER' else f'Có đồ chưa có người trông coi tại {d["table_name"]}. Vui lòng kiểm tra.'
                events.append(event)
            decisions.append(d)
        if valid:
            # Store last non-deadband point, so a hysteresis crossing still intersects.
            self.previous={pid:self._point(tr,observation,True) if next(iter(self.engines.values()))._side(self._point(tr,observation,True)) is not None else self.previous.get(pid,self._point(tr,observation,True)) for pid,tr in people.items()}
        priorities={'ALERT':6,'OWNER_LEFT':5,'UNCERTAIN':4,'ATTENDED':3,'UNASSIGNED':2,'RESOLVED':1}
        top=dict(max(decisions,key=lambda d:priorities.get(d['state'],0)));top['tables']=decisions;top['events']=events;top['mode']='classroom';top['requires_recalibration']=self.camera_moved
        return top
