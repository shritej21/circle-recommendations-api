
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    topic: float
    activity: float
    freshness: float
    accessibility: float


class CircleRecommendation(BaseModel):
    circle_id: int
    name: str
    description: str
    topic: str | None = None
    format: str
    member_count: int
    score: float
    score_breakdown: ScoreBreakdown
    explanation: str


class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: list[CircleRecommendation] = Field(default_factory=list)
