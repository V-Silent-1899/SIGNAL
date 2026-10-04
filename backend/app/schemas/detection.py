from typing import List, Optional
from pydantic import BaseModel

class DetectionBox(BaseModel):
    box_id: Optional[str] = None
    track_id: Optional[int] = None
    class_id: int
    class_name: str
    confidence: float
    # Normalized coordinates [x1, y1, x2, y2] in range 0.0 - 1.0
    bbox_normalized: List[float]

class PoseKeypoint(BaseModel):
    id: int
    name: str
    x: float
    y: float
    confidence: float

class PoseSkeleton(BaseModel):
    track_id: Optional[int] = None
    person_id: Optional[str] = None
    confidence: float
    keypoints: List[PoseKeypoint]
    bbox_normalized: Optional[List[float]] = None

class FrameDetections(BaseModel):
    frame_idx: int
    timestamp: float
    boxes: List[DetectionBox]
    skeletons: List[PoseSkeleton]

class DetectionsResponse(BaseModel):
    video_id: str
    total_frames: int
    frames: List[FrameDetections]

class TrackItem(BaseModel):
    track_id: int
    class_name: str
    start_time: float
    end_time: float
    duration: float
    total_detections: int
    avg_confidence: float
    trajectory: List[List[float]] # [[timestamp, x_center, y_center], ...]

class TracksResponse(BaseModel):
    video_id: str
    total_tracks: int
    tracks: List[TrackItem]
