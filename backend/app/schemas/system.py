from typing import List, Optional
from pydantic import BaseModel

class ModelStatus(BaseModel):
    name: str
    status: str  # "ONLINE", "DEGRADED", "OFFLINE"
    version: Optional[str] = None
    device: Optional[str] = None
    details: Optional[str] = None

class SystemStatusResponse(BaseModel):
    status: str  # "ONLINE", "DEGRADED", "OFFLINE"
    gpu_available: bool
    gpu_name: Optional[str] = None
    vram_mb: Optional[int] = None
    cpu_count: int
    ram_gb: float
    ffmpeg_available: bool
    ffmpeg_path: Optional[str] = None
    models: List[ModelStatus]
