from typing import List, Optional
from pydantic import BaseModel

class EventItem(BaseModel):
    id: str
    video_id: str
    timestamp_start: float
    timestamp_end: float
    title: str
    description: str
    importance: str = "medium"  # "high", "medium", "low"
    confidence: float
    subjects: List[str] = []
    objects: List[str] = []
    evidence_frames: List[int] = []
    evidence_urls: List[str] = []
    created_at: Optional[str] = None

class EventsResponse(BaseModel):
    video_id: str
    total_events: int
    events: List[EventItem]

class StructuredExtractionResult(BaseModel):
    events: List[EventItem]
