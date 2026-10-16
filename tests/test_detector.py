import json
import unittest
from types import SimpleNamespace
import numpy as np
from detector import Detector

class Array:
    def __init__(self, values): self.values = values
    def cpu(self): return self
    def tolist(self): return self.values

class FakeModel:
    names = {0: 'person', 24: 'backpack'}
    predictor = None
    def track(self, frame, **kwargs):
        self.kwargs = kwargs
        boxes = SimpleNamespace(xyxy=Array([[-2, 1, 200, 70], [4, 5, 30, 40]]),
                                conf=Array([.8, .7]), cls=Array([0,24]), id=Array([1,2]))
        return [SimpleNamespace(boxes=boxes)]

class DetectorTests(unittest.TestCase):
    def test_contract_and_reset(self):
        detector = Detector('unused.pt', {})
        detector._model = FakeModel()
        result = detector.infer(np.full((60,100,3), 100, np.uint8), 0, 0.)
        json.dumps(result, allow_nan=False)
        self.assertEqual(result['tracks'][0]['bbox_xyxy'], [0.,1.,100.,60.])
        self.assertTrue(all(t['observed'] for t in result['tracks']))
        self.assertEqual(detector._model.kwargs['tracker'], 'bytetrack.yaml')
        detector.infer(np.zeros((60,100,3), np.uint8), 1, 1.)
        with self.assertRaises(ValueError): detector.infer(np.zeros((60,100,3), np.uint8), 2, .5)
        detector.reset()
        self.assertEqual(detector.infer(np.zeros((60,100,3), np.uint8), 0, 0.)['quality_reasons'], ['too_dark'])

    def test_untracked_measurements_have_null_id(self):
        detector = Detector('unused.pt', {})
        detector._model = FakeModel()
        original = detector._model.track
        def track(frame, **kwargs):
            output = original(frame, **kwargs)
            output[0].boxes.id = None
            return output
        detector._model.track = track
        result = detector.infer(np.full((60,100,3), 100, np.uint8), 0, 0.)
        self.assertIsNone(result['tracks'][0]['id'])

    def test_invalid_frame(self):
        with self.assertRaises(ValueError): Detector('unused.pt', {}).infer(np.zeros((2,2)),0,0.)

if __name__ == '__main__': unittest.main()
