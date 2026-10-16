import unittest
import cv2
import numpy as np
from camera_quality import MotionGuard

class MotionTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(42);self.image=rng.integers(0,255,(240,320,3),dtype=np.uint8)
    def test_static(self):
        g=MotionGuard();g.update(self.image);self.assertTrue(g.update(self.image.copy())['stable'])
    def test_global_shift(self):
        g=MotionGuard();g.update(self.image)
        shifted=cv2.warpAffine(self.image,np.float32([[1,0,14],[0,1,0]]),(320,240))
        self.assertEqual(g.update(shifted)['reason'],'camera_moved')
    def test_local_object(self):
        g=MotionGuard();g.update(self.image);changed=self.image.copy();changed[70:100,90:120]=0
        self.assertTrue(g.update(changed)['stable'])
    def test_low_texture_uncertain(self):
        g=MotionGuard();blank=np.zeros_like(self.image);g.update(blank)
        self.assertFalse(g.update(blank)['stable'])
    def test_slow_cumulative_pan(self):
        g=MotionGuard();g.update(self.image)
        moved=False
        for shift in range(1,9):
            frame=cv2.warpAffine(self.image,np.float32([[1,0,shift],[0,1,0]]),(320,240))
            moved=moved or g.update(frame)['reason']=='camera_moved'
        self.assertTrue(moved)
