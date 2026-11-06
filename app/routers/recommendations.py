
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import User
from app.schemas import (
    CircleRecommendation,
    RecommendationResponse,
    ScoreBreakdown,
)
from app.services.recommendation import recommend_circles
from app.services.explanations import generate_explanation


router = APIRouter(prefix="/api", tags=["Recommendations"])


@router.get(
    "/users/{user_id}/recommendations",
    response_model=RecommendationResponse,
)
def get_recommendations(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    
    user = (
        db.query(User)
        .options(selectinload(User.interests))
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_id} not found",
        )

    
    ranked_results = recommend_circles(
        db=db,
        user_id=user_id,
        limit=limit,
    )

    recommendations = []

    for result in ranked_results:
        circle = result["circle"]

        explanation = generate_explanation(
            user=user,
            circle=circle,
            recommendation=result,
        )

        recommendations.append(
            CircleRecommendation(
                circle_id=circle.id,
                name=circle.name,
                description=circle.description or "",
                topic=circle.topic,
                format=circle.format,
                member_count=circle.member_count,
                score=round(result["score"], 2),
                score_breakdown=ScoreBreakdown(
                    topic=round(result["topic_score"], 2),
                    activity=round(result["activity_score"], 2),
                    freshness=round(result["freshness_score"], 2),
                    accessibility=round(
                        result["accessibility_score"], 2
                    ),
                ),
                explanation=explanation,
            )
        )

    return RecommendationResponse(
        user_id=user_id,
        recommendations=recommendations,
    )
