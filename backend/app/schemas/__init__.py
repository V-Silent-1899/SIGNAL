from backend.app.schemas.video import VideoMetadata, VideoResponse, UploadResponse
from backend.app.schemas.detection import (
    DetectionBox,
    PoseKeypoint,
    PoseSkeleton,
    FrameDetections,
    DetectionsResponse,
    TrackItem,
    TracksResponse,
)
from backend.app.schemas.event import EventItem, EventsResponse
from backend.app.schemas.qa import QuestionRequest, QuestionResponse, EvidenceItem
from backend.app.schemas.system import ModelStatus, SystemStatusResponse
from backend.app.schemas.analysis import AnalysisStatusResponse

__all__ = [
    "VideoMetadata",
    "VideoResponse",
    "UploadResponse",
    "DetectionBox",
    "PoseKeypoint",
    "PoseSkeleton",
    "FrameDetections",
    "DetectionsResponse",
    "TrackItem",
    "TracksResponse",
    "EventItem",
    "EventsResponse",
    "QuestionRequest",
    "QuestionResponse",
    "EvidenceItem",
    "ModelStatus",
    "SystemStatusResponse",
    "AnalysisStatusResponse",
]
