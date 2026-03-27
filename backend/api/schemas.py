from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Preset(str, Enum):
    NORMAL = "normal"
    P0_CRITICAL = "p0_critical"
    INNOVATION = "innovation"


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    file_type: str
    size: int


class StartReviewRequest(BaseModel):
    session_id: str
    preset: Preset = Preset.NORMAL


class StartReviewResponse(BaseModel):
    status: str
    session_id: str


class DimensionScore(BaseModel):
    dimension: str
    score: float
    issues: list


class ReviewStatus(BaseModel):
    session_id: str
    status: str
    current_dimension: Optional[str] = None
    completed_dimensions: list[str] = []
    progress: float


class ReviewReport(BaseModel):
    project_name: str
    version: str
    review_date: str
    preset: str
    total_score: float
    recommendation: str
    dimension_scores: list[DimensionScore]
    issues: list
    summary: str


class SSEProgressEvent(BaseModel):
    dimension: str
    status: str
    score: Optional[float] = None
    issues: Optional[list] = None


class SSEStreamingEvent(BaseModel):
    content: str


class SSECompleteEvent(BaseModel):
    report: ReviewReport
