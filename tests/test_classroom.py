import json
import unittest
from pathlib import Path
from classroom_engine import ClassroomEngine, validate_classroom_config
from test_engine import obs

CFG=json.loads(Path('config.json').read_text(encoding='utf-8-sig'))
CFG.update(mode='classroom',geometry_calibrated=True,tables=[{'id':'T1','name':'Bàn 1','polygon_norm':[[.3,.4],[.65,.4],[.65,.8],[.3,.8]]}],door_polygon_norm=[[.7,.4],[.9,.4],[.9,.8],[.7,.8]],exit_line_norm=[[.75,.4],[.75,.8]])

class ClassroomTests(unittest.TestCase):
    def setUp(self): self.e=ClassroomEngine(CFG)
    def attend(self):
        for i in range(6): d=self.e.update(obs(i*.5))
        self.assertTrue(d['tables'][0]['associated'])
    def test_doorway_alert(self):
        self.attend();d=self.e.update(obs(3,.82));self.assertEqual(len(d['events']),1)
        self.assertEqual(d['tables'][0]['episode_id'],d['events'][0]['episode_id'])
        self.assertIn('Bàn 1',d['events'][0]['announcement_text'])
        for i in range(7,17): d=self.e.update(obs(i*.5,None))
        self.assertEqual(d['state'],'ALERT');self.assertEqual(d['events'][0]['seat_id'],'T1')
        self.assertEqual(d['tables'][0]['episode_id'],d['events'][0]['episode_id'])
    def test_crossing_outside_door_rejected(self):
        self.attend()
        o=obs(3,.82);o['tracks'][0]['bbox_xyxy']=[77,0,87,20]
        d=self.e.update(o);self.assertFalse(d['events']);self.assertEqual(d['state'],'UNCERTAIN')
    def test_motion_latches_until_new_engine(self):
        self.attend();o=obs(3);o['quality_reasons']=['camera_moved'];d=self.e.update(o)
        self.assertEqual(d['reason'],'CAMERA_MOVED_RECALIBRATION_REQUIRED')
        self.assertEqual(self.e.update(obs(3.5,.82))['reason'],d['reason'])
        self.e.reset();self.assertEqual(self.e.update(obs(0))['reason'],d['reason'])
        self.assertNotEqual(ClassroomEngine(CFG).update(obs(0))['reason'],d['reason'])
    def test_bag_leaving_table_not_confirmed(self):
        self.attend();d=self.e.update(obs(3,.82,bx=.9));self.assertFalse(d['events'])
    def test_uncalibrated(self):
        d=ClassroomEngine(dict(CFG,geometry_calibrated=False)).update(obs(0))
        self.assertEqual(d['state'],'UNCERTAIN')
    def test_invalid_geometry(self):
        with self.assertRaises(ValueError):validate_classroom_config(dict(CFG,tables=[]))
        with self.assertRaises(ValueError):validate_classroom_config(dict(CFG,door_polygon_norm=[[0,0],[0,0],[0,0]]))
    def test_reset_does_not_duplicate_episode(self):
        self.attend();one=self.e.update(obs(3,.82))['events'][0]
        self.e.reset();self.attend();two=self.e.update(obs(3,.82))['events'][0]
        self.assertNotEqual(one['event_id'],two['event_id'])

class MoreClassroomTests(unittest.TestCase):
    setUp = ClassroomTests.setUp
    attend = ClassroomTests.attend
    def test_same_person_near_two_tables_ambiguous(self):
        cfg=dict(CFG,tables=[{'id':'T1','name':'Bàn 1','polygon_norm':[[.3,.4],[.55,.4],[.55,.8],[.3,.8]]},{'id':'T2','name':'Bàn 2','polygon_norm':[[.56,.4],[.7,.4],[.7,.8],[.56,.8]]}])
        e=ClassroomEngine(cfg)
        for i in range(6):
            o=obs(i*.5,.56)
            o['tracks'].append(dict(id=8,class_name='backpack',bbox_xyxy=[60,55,66,65],confidence=.9,observed=True))
            d=e.update(o)
        self.assertFalse(any(x['associated'] for x in d['tables']))
    def test_gap_invalidates_door_crossing(self):
        self.attend();d=self.e.update(obs(4,.82));self.assertFalse(d['events'])
    def test_lost_owner_no_door_event(self):
        self.attend()
        for i in range(6,20):d=self.e.update(obs(i*.5,None))
        self.assertEqual(d['state'],'UNCERTAIN');self.assertFalse(d['events'])
    def test_hysteresis_crossing(self):
        self.attend();self.e.update(obs(3,.75));d=self.e.update(obs(3.5,.82))
        self.assertTrue(d['events'][0]['room_exit_confirmed'])

    def test_lowtexture_is_recoverable_not_motion_latch(self):
        self.attend()
        o=obs(3);o['quality_ok']=False;o['quality_reasons']=['insufficient_motion_features']
        d=self.e.update(o);self.assertEqual(d['state'],'UNCERTAIN');self.assertFalse(d['requires_recalibration'])
        for i in range(7,13):d=self.e.update(obs(i*.5))
        self.assertEqual(d['state'],'ATTENDED');self.assertFalse(d['requires_recalibration'])
    def test_line_crossing_outside_door_polygon(self):
        cfg=dict(CFG,exit_line_norm=[[.75,0],[.75,1]],door_polygon_norm=[[.7,.75],[.9,.75],[.9,.95],[.7,.95]])
        e=ClassroomEngine(cfg)
        for i in range(6):e.update(obs(i*.5))
        d=e.update(obs(3,.82));self.assertFalse(d['events']);self.assertEqual(d['reason'],'NO_VERIFIED_DOORWAY_CROSSING')
