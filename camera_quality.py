"""Global camera-motion evidence; not a SLAM or stabilization implementation."""
from math import atan2, degrees, hypot
import cv2
import numpy as np


class MotionGuard:
    def __init__(self,config=None):
        self.config=config or {};self.reset()

    def reset(self):self.previous=None

    def update(self,frame):
        if frame is None or not getattr(frame,'size',0):return dict(stable=False,reason='invalid_motion_frame',score=0.0)
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) if frame.ndim==3 else frame.copy()
        scale=min(1,480/gray.shape[1]);gray=cv2.resize(gray,None,fx=scale,fy=scale)
        previous=self.previous
        if previous is None:
            self.previous=gray
            return dict(stable=True,reason='motion_reference_initialized',score=0.0)
        if previous.shape!=gray.shape:return dict(stable=False,reason='camera_moved',score=1.0)
        points=cv2.goodFeaturesToTrack(previous,maxCorners=250,qualityLevel=.015,minDistance=7)
        if points is None or len(points)<16:return dict(stable=False,reason='insufficient_motion_features',score=0.0)
        next_points,status,_=cv2.calcOpticalFlowPyrLK(previous,gray,points,None)
        if next_points is None:return dict(stable=False,reason='motion_estimation_failed',score=0.0)
        valid=status.ravel()==1;a=points[valid].reshape(-1,2);b=next_points[valid].reshape(-1,2)
        if len(a)<16:return dict(stable=False,reason='insufficient_motion_features',score=0.0)
        transform,inliers=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=2)
        if transform is None or inliers is None:return dict(stable=False,reason='motion_estimation_failed',score=0.0)
        ratio=float(inliers.mean());height,width=gray.shape
        if ratio<.55:return dict(stable=False,reason='motion_estimation_unreliable',score=0.0)
        displacement=float(np.median(np.linalg.norm(b-a,axis=1)))/hypot(width,height)
        rotation=abs(degrees(atan2(transform[1,0],transform[0,0])))
        zoom=abs(hypot(transform[0,0],transform[1,0])-1)
        moved=ratio>=.55 and (displacement>self.config.get('camera_motion_threshold_norm',.008) or rotation>1.0 or zoom>.015)
        return dict(stable=not moved,reason='camera_moved' if moved else 'camera_stable',score=round(displacement,6))
