from typing import Optional
from pydantic import BaseModel

class AnalysisStatusResponse(BaseModel):
    video_id: str
    job_id: str
    status: str  # "IDLE", "PROCESSING", "COMPLETED", "FAILED"
    stage: str   # "INGESTION", "EXTRACTION", "DETECTION", "TRACKING", "POSE", "UNDERSTANDING", "EVENTS", "INDEXING", "DONE"
    progress: float  # 0.0 to 100.0
    stage_message: str
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    is_demo: bool = False
