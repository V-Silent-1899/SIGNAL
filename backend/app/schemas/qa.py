from typing import List, Optional
from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str

class EvidenceItem(BaseModel):
    timestamp: float
    frame_idx: int
    image_url: str
    description: str

class QuestionResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    timestamps: List[float]
    primary_timestamp: Optional[float] = None
    related_event_ids: List[str] = []
    evidence: List[EvidenceItem] = []
    explanation: str
