"""Measured-track spatial/temporal rules; track IDs are not verified identities."""
from math import hypot, isfinite


class EventEngine:
    def __init__(self, config: dict):
        self.config = config
        self.reset()

    def reset(self) -> None:
        self.last_t_s = None
        self.person_id = self.object_id = None
        self.anchor = None
        self.stationary_since = None
        self.candidate = None
        self.candidate_since = None
        self.duration = 0.0
        self.distance = None
        self.last_side = None
        self.t_exit = None
        self.episode = 0
        self.emitted = set()

    def _point(self, track, width, height, person=False):
        x1,y1,x2,y2=track['bbox_xyxy']
        return ((x1+x2)/2/width, (y2 if person else (y1+y2)/2)/height)

    def _inside(self, p):
        poly=self.config['roi_norm']
        inside=False
        x,y=p
        for a,b in zip(poly,poly[1:]+poly[:1]):
            if (a[1]>y)!=(b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
                inside=not inside
        return inside

    def _side(self,p):
        a,b=self.config['exit_line_norm']
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=hypot(dx,dy)
        if length==0: raise ValueError('exit line has zero length')
        cross=(dx*(p[1]-a[1])-dy*(p[0]-a[0]))/length
        # For a downward vertical line, positive cross means image-left.
        signed=cross if self.config.get('inside_side','left')=='left' else -cross
        h=self.config.get('exit_hysteresis_norm',.02)
        return 'inside' if signed>h else 'outside' if signed < -h else None

    def _interrupt(self):
        self.t_exit=None
        self.last_side=None
        self.candidate=None
        self.candidate_since=None
        self.anchor=None
        self.stationary_since=None

    def _decision(self,state,reason,t,stationary=False,events=None):
        elapsed=max(0,t-self.t_exit) if self.t_exit is not None else 0.0
        return dict(state=state,reason=reason,seat_id=self.config['seat_id'],
                    person_id=self.person_id,object_id=self.object_id,
                    stationary=stationary,associated=self.person_id is not None,
                    t_exit_s=self.t_exit,
                    leave_confirmed=self.t_exit is not None and elapsed>=self.config['leave_confirm_s'],
                    elapsed_since_exit_s=elapsed,
                    remaining_s=max(0,self.config['alert_after_exit_s']-elapsed) if self.t_exit is not None else None,
                    events=events or [],association_method='sustained_unique_proximity_and_stationary_object',
                    association_duration_s=self.duration,association_distance_norm=self.distance,
                    technology='YOLO detector + tracker IDs + normalized image geometry + temporal rules',
                    certainty='rule_based_evidence_not_calibrated_probability' if self.person_id is not None else 'unassigned',
                    geometry_calibrated=bool(self.config.get('geometry_calibrated',False)))

    def _event(self,kind,t,reason):
        key=(self.episode,kind)
        if key in self.emitted: return []
        self.emitted.add(key)
        session=str(self.config.get('session_id','session'))
        return [dict(event_id=f'{session}:{self.episode}:{kind}',episode_id=self.episode,
                     type=kind,t_s=t,seat_id=self.config['seat_id'],person_id=self.person_id,
                     object_id=self.object_id,reason=reason)]

    def update(self, observation: dict) -> dict:
        t=float(observation['t_s'])
        if not isfinite(t) or t<0: raise ValueError('invalid timestamp')
        if self.last_t_s is not None and t<self.last_t_s: raise ValueError('timestamp moved backwards')
        gap=self.last_t_s is not None and t-self.last_t_s>self.config['max_frame_gap_s']
        self.last_t_s=t
        if gap or not observation.get('quality_ok',False):
            self._interrupt()
            return self._decision('UNCERTAIN','FRAME_GAP' if gap else 'IMAGE_QUALITY',t)
        w,h=observation['width'],observation['height']
        if w<=0 or h<=0: raise ValueError('invalid image dimensions')
        tracks=[x for x in observation['tracks'] if x.get('observed') is True
                and x.get('id') is not None and x.get('confidence',0)>=self.config['confidence_min']]
        people={x['id']:x for x in tracks if x['class_name']=='person'}
        bags=[x for x in tracks if x['class_name'] in self.config.get('object_classes',['backpack','handbag','suitcase'])]
        if self.object_id is not None:
            bag=next((x for x in bags if x['id']==self.object_id),None)
        else:
            eligible=[x for x in bags if self._inside(self._point(x,w,h))]
            bag=eligible[0] if len(eligible)==1 else None
        if bag is None:
            self._interrupt()
            return self._decision('UNCERTAIN' if self.object_id is not None or bags else 'UNASSIGNED',
                                  'OBJECT_MISSING_OR_AMBIGUOUS',t)
        bp=self._point(bag,w,h)
        if self.object_id is None: self.object_id=bag['id']
        if self.anchor is None or hypot(bp[0]-self.anchor[0],bp[1]-self.anchor[1])>self.config['stationary_radius_norm']:
            self.anchor=bp
            self.stationary_since=t
            self.candidate=None
            self.candidate_since=None
        stationary=t-self.stationary_since>=self.config['stationary_s']
        if self.person_id is None:
            close=[]
            for pid,p in people.items():
                pp=self._point(p,w,h,True)
                distance=hypot(pp[0]-bp[0],pp[1]-bp[1])
                if distance<=self.config['association_distance_norm'] and self._side(pp)=='inside': close.append((pid,distance))
            if len(close)!=1:
                self.candidate=self.candidate_since=None
                return self._decision('UNASSIGNED','NO_UNIQUE_NEARBY_PERSON',t,stationary)
            pid,distance=close[0]
            if self.candidate!=pid:
                self.candidate,self.candidate_since=pid,t
            self.duration=t-self.candidate_since
            self.distance=distance
            if not stationary or self.duration<self.config['association_s']:
                return self._decision('UNASSIGNED','COLLECTING_ASSOCIATION_EVIDENCE',t,stationary)
            self.person_id=pid
            self.last_side='inside'
        owner=people.get(self.person_id)
        side=self._side(self._point(owner,w,h,True)) if owner else None
        if self.t_exit is not None:
            if side=='inside':
                self.t_exit=None
                self.last_side='inside'
                return self._decision('ATTENDED','OWNER_RETURNED',t,stationary)
            if not stationary:
                self._interrupt()
                return self._decision('UNCERTAIN','OBJECT_MOVED_DURING_EXIT',t,stationary)
            elapsed=t-self.t_exit
            if elapsed>=max(self.config['leave_confirm_s'],self.config['alert_after_exit_s']):
                events=self._event('UNATTENDED_ALERT',t,'OBJECT_REMAINS_AFTER_CONFIRMED_EXIT')
                return self._decision('ALERT','OBJECT_REMAINS_AFTER_CONFIRMED_EXIT',t,stationary,events)
            return self._decision('OWNER_LEFT','WAITING_AFTER_CROSSING',t,stationary)
        if owner is None:
            self.last_side=None
            return self._decision('UNCERTAIN','OWNER_NOT_OBSERVED_NO_CROSSING',t,stationary)
        if side=='outside' and self.last_side=='inside' and stationary:
            self.t_exit=t
            self.episode+=1
            self.last_side='outside'
            events=self._event('REMINDER',t,'ASSOCIATED_PERSON_CROSSED_EXIT_OBJECT_REMAINS')
            return self._decision('OWNER_LEFT','ASSOCIATED_PERSON_CROSSED_EXIT_OBJECT_REMAINS',t,stationary,events)
        if side is not None: self.last_side=side
        if side=='outside':
            return self._decision('UNCERTAIN','OWNER_OUTSIDE_WITHOUT_CONTINUOUS_CROSSING',t,stationary)
        return self._decision('ATTENDED','ASSOCIATED_PERSON_PRESENT',t,stationary)
