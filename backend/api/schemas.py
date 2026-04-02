from typing import Any, Optional
from enum import Enum

from pydantic import BaseModel, Field


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


class ReviewIssueEvidence(BaseModel):
    display_id: str
    issue_key: str
    source_quote: str = ""
    source_section: str = ""
    source_locator: str = ""


class ReviewIssue(BaseModel):
    id: str
    display_id: str
    issue_key: str
    severity: str
    title: str
    dimension: str
    description: str
    suggestion: str = ""
    source_quote: str = ""
    source_section: str = ""
    source_locator: str = ""
    evidence: ReviewIssueEvidence


class ReviewStatus(BaseModel):
    session_id: str
    status: str
    current_dimension: Optional[str] = None
    completed_dimensions: list[str] = Field(default_factory=list)
    progress: float


class ReviewReport(BaseModel):
    project_name: str
    version: str
    review_date: str
    preset: str
    total_score: float
    recommendation: str
    dimension_scores: list[DimensionScore]
    issues: list[ReviewIssue]
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


class ChatRequest(BaseModel):
    session_id: str
    message: str
    selected_issue_id: Optional[str] = None
    context_mode: str = "default"


class SuggestedAction(BaseModel):
    type: str
    label: str
    issue_id: Optional[str] = None
    preset: Optional[str] = None


class SourceRef(BaseModel):
    type: str
    id: Optional[str] = None
    name: Optional[str] = None
    excerpt: Optional[str] = None


class RunStateSummary(BaseModel):
    status: str
    progress: float
    current_dimension: Optional[str] = None
    completed_dimensions: list[str] = Field(default_factory=list)
    total_score: Optional[float] = None
    recommendation: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    response_mode: str
    assistant_status: str
    selected_issue: Optional[dict] = None
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)
    target_issue_id: Optional[str] = None
    run_state: RunStateSummary


class AgentConfig(BaseModel):
    """Agent configuration for review session."""
    enable_dev_agent: bool = True   # 关联研发 Agent
    enable_design_agent: bool = False  # 关联设计 Agent
    enable_test_agent: bool = True   # 关联测试 Agent


class AgentConfigRequest(BaseModel):
    session_id: str
    config: AgentConfig


class AgentConfigResponse(BaseModel):
    session_id: str
    config: AgentConfig
    status: str


class ResetResponse(BaseModel):
    session_id: str
    status: str
    message: str


class ShareResponse(BaseModel):
    share_token: str
    share_url: str
    expires_in: int  # seconds
