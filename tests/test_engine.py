import json
import unittest
from pathlib import Path
from event_engine import EventEngine

CFG = json.loads(Path('config.json').read_text(encoding='utf-8-sig'))

def obs(t, px=.5, bag=True, people=None, quality=True, observed=True, bx=.5):
    tracks=[]
    if people is None:
        people=[] if px is None else [(1,px)]
    for pid,x in people:
        tracks.append(dict(id=pid,class_name='person',bbox_xyxy=[(x-.05)*100,20,(x+.05)*100,60],confidence=.9,observed=observed))
    if bag:
        tracks.append(dict(id=7,class_name='backpack',bbox_xyxy=[(bx-.03)*100,55,(bx+.03)*100,65],confidence=.9,observed=observed))
    return dict(frame_id=int(t*10),t_s=t,width=100,height=100,quality_ok=quality,tracks=tracks)

class EngineTests(unittest.TestCase):
    def setUp(self): self.e=EventEngine(CFG)
    def attend(self):
        for i in range(6): d=self.e.update(obs(i*.5))
        self.assertTrue(d['associated'])
        return d
    def leave(self):
        self.attend()
        return self.e.update(obs(3,.82))
    def test_sustained_association(self):
        self.assertFalse(self.e.update(obs(0))['associated'])
        d=self.attend()
        self.assertEqual(d['person_id'],1)
        self.assertIn('association_method',d)
    def test_alert_and_dedup(self):
        d=self.leave()
        self.assertEqual([x['type'] for x in d['events']],['REMINDER'])
        for i in range(7,16):
            d=self.e.update(obs(i*.5,None))
            self.assertEqual(d['events'],[])
        d=self.e.update(obs(8,None))
        self.assertEqual([x['type'] for x in d['events']],['UNATTENDED_ALERT'])
        self.assertEqual(self.e.update(obs(8.5,None))['events'],[])
    def test_occlusion_not_exit(self):
        self.attend()
        d=self.e.update(obs(3,None))
        self.assertEqual(d['state'],'UNCERTAIN')
        self.assertEqual(d['events'],[])
    def test_prediction_not_measurement(self):
        self.attend()
        self.assertEqual(self.e.update(obs(3,.82,observed=False))['state'],'UNCERTAIN')
    def test_return_cancels(self):
        self.leave()
        d=self.e.update(obs(3.5,.5))
        self.assertEqual(d['state'],'ATTENDED')
        self.assertIsNone(d['t_exit_s'])
    def test_missing_bag_cancels_exit_evidence(self):
        self.leave()
        self.assertEqual(self.e.update(obs(3.5,None,bag=False))['state'],'UNCERTAIN')
        for i in range(8,18): d=self.e.update(obs(i*.5,None))
        self.assertEqual(d['events'],[])
    def test_gap_requires_new_crossing(self):
        self.leave()
        self.assertEqual(self.e.update(obs(6,None))['state'],'UNCERTAIN')
        for i in range(13,21): d=self.e.update(obs(i*.5,None))
        self.assertEqual(d['events'],[])
    def test_passerby_not_owner(self):
        self.attend()
        d=self.e.update(obs(3,people=[(1,.5),(2,.51)]))
        self.assertEqual(d['person_id'],1)
    def test_ambiguous_no_assignment(self):
        for i in range(8): d=self.e.update(obs(i*.5,people=[(1,.5),(2,.51)]))
        self.assertFalse(d['associated'])
    def test_slow_motion_not_stationary(self):
        for i in range(6): d=self.e.update(obs(i*.5,bx=.5+i*.02))
        self.assertFalse(d['stationary'])
    def test_quality_and_reset(self):
        self.attend()
        self.assertEqual(self.e.update(obs(3,quality=False))['state'],'UNCERTAIN')
        self.e.reset()
        self.assertFalse(self.e.update(obs(0))['associated'])
    def test_backwards(self):
        self.e.update(obs(1))
        with self.assertRaises(ValueError): self.e.update(obs(0))



class EngineEdgeTests(unittest.TestCase):
    setUp = EngineTests.setUp
    attend = EngineTests.attend
    leave = EngineTests.leave
    def test_new_episode_after_return(self):
        first=self.leave()['events'][0]
        self.e.update(obs(3.5,.5))
        second=self.e.update(obs(4,.82))['events'][0]
        self.assertNotEqual(first['episode_id'],second['episode_id'])
        self.assertNotEqual(first['event_id'],second['event_id'])
    def test_changed_owner_id_not_assigned(self):
        self.attend()
        for i in range(6,15): d=self.e.update(obs(i*.5,people=[(2,.5)]))
        self.assertEqual(d['person_id'],1)
        self.assertEqual(d['state'],'UNCERTAIN')
        self.assertFalse(d['leave_confirmed'])
    def test_low_confidence_not_evidence(self):
        for i in range(8):
            o=obs(i*.5)
            for track in o['tracks']: track['confidence']=.1
            d=self.e.update(o)
        self.assertFalse(d['associated'])
    def test_hysteresis_keeps_inside_until_outside(self):
        self.attend()
        self.assertEqual(self.e.update(obs(3,.75))['events'],[])
        self.assertEqual(self.e.update(obs(3.5,.78))['events'][0]['type'],'REMINDER')
    def test_multiple_objects_require_reset_selection(self):
        for i in range(8):
            o=obs(i*.5)
            o['tracks'].append(dict(id=8,class_name='backpack',bbox_xyxy=[40,55,46,65],confidence=.9,observed=True))
            d=self.e.update(o)
        self.assertFalse(d['associated'])
    def test_evidence_serializable_and_honest(self):
        d=self.attend()
        json.dumps(d,allow_nan=False)
        self.assertEqual(d['certainty'],'rule_based_evidence_not_calibrated_probability')
        self.assertFalse(d['geometry_calibrated'])
    def test_invalid_timestamp_rejected(self):
        with self.assertRaises(ValueError): self.e.update(obs(0) | {'t_s':float('nan')})

if __name__=='__main__': unittest.main()

