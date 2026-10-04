from typing import Optional
from pydantic import BaseModel

class VideoMetadata(BaseModel):
    duration: float
    fps: float
    total_frames: int
    width: int
    height: int
    codec: Optional[str] = None
    file_size: int

class VideoResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    duration: Optional[float] = None
    status: str
    created_at: str
    metadata: Optional[VideoMetadata] = None

class UploadResponse(BaseModel):
    video_id: str
    filename: str
    message: str
    metadata: VideoMetadata
