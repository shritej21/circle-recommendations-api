
from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models import User, Circle, Activity


def get_reference_time(circles):
    """
    Use the latest Circle activity timestamp as the
    reference point for freshness calculations.
    """

    timestamps = [
        circle.last_activity_at
        for circle in circles
        if circle.last_activity_at is not None
    ]

    return max(timestamps) if timestamps else None


def calculate_topic_score(user, circle):
    """
    Calculate relevance using the user's interests.

    Primary topic match: 45 points.
    Secondary topic matches: proportional score.
    """

    interests = {topic.slug for topic in user.interests}

    if not interests:
        return 0.0

    circle_topics = {topic.slug for topic in circle.topics}

    
    if circle.topic in interests:
        return 45.0

    
    matches = interests & circle_topics

    if not matches:
        return 0.0

    return 45.0 * min(
        1.0,
        len(matches) / len(interests)
    )


def calculate_activity_score(
    circle,
    max_activity,
    engagement_by_circle,
):
    """
    Calculate activity using:
    - Feed posts
    - Group chat messages
    - Reactions
    - Comments
    - Saves
    """

    activity = (
        2 * circle.feed_posts_30d
        + circle.chat_messages_30d
        + engagement_by_circle.get(circle.id, 0)
    )

    if max_activity <= 0:
        return 0.0

    return 25.0 * min(
        1.0,
        activity / max_activity
    )


def calculate_freshness_score(circle, reference_time):
    """
    Reward Circles with recent activity.

    Activity within 30 days receives a freshness score.
    """

    if not circle.last_activity_at or not reference_time:
        return 0.0

    days_old = (
        reference_time - circle.last_activity_at
    ).total_seconds() / 86400

    if days_old < 0 or days_old > 30:
        return 0.0

    return 20.0 * (1 - days_old / 30)


def calculate_accessibility_score(circle):
    """
    Reward Circles that are easier to join.
    """

    if circle.join_policy == "open":
        return 10.0

    if circle.join_policy == "request":
        return 7.0

    return 0.0

def get_engagement_by_circle(db, reference_time):
    """
    Aggregate reactions, comments and saves
    for activity records from the last 30 days.

    Comments and saves receive additional weight.
    """

    if reference_time is None:
        return {}

    cutoff = reference_time - timedelta(days=30)

    results = (
        db.query(
            Activity.circle_id,
            func.sum(
                Activity.reaction_count
                + 2 * Activity.comment_count
                + 2 * Activity.save_count
            ).label("engagement")
        )
        .filter(Activity.created_at >= cutoff)
        .group_by(Activity.circle_id)
        .all()
    )

    return {
        circle_id: engagement or 0
        for circle_id, engagement in results
    }


def recommend_circles(
    db: Session,
    user_id: int,
    limit: int = 10,
):
    """
    Return ranked and diverse Circle recommendations.

    Pipeline:
    1. Retrieve user and Circles.
    2. Filter ineligible Circles.
    3. Aggregate engagement.
    4. Calculate weighted scores.
    5. Rank recommendations.
    6. Apply topic diversity.
    """

    if limit < 1:
        raise ValueError("Limit must be greater than zero")
    user = (
        db.query(User)
        .options(
            selectinload(User.interests),
            selectinload(User.memberships),
        )
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise ValueError(f"User {user_id} not found")
    circles = (
        db.query(Circle)
        .options(selectinload(Circle.topics))
        .all()
    )

    reference_time = get_reference_time(circles)

    
    existing_ids = {
        membership.circle_id
        for membership in user.memberships
    }


    candidates = []

    for circle in circles:

        if circle.id in existing_ids:
            continue
        if circle.access != "public":
            continue

        if circle.join_policy not in {"open", "request"}:
            continue

        if (
            circle.max_members is not None
            and circle.member_count >= circle.max_members
        ):
            continue
        if reference_time is not None:

            if circle.last_activity_at is None:
                continue

            if (
                reference_time - circle.last_activity_at
                > timedelta(days=30)
            ):
                continue

        candidates.append(circle)

    if not candidates:
        return []

    engagement_by_circle = get_engagement_by_circle(
        db,
        reference_time,
    )

    max_activity = max(
        (
            2 * circle.feed_posts_30d
            + circle.chat_messages_30d
            + engagement_by_circle.get(circle.id, 0)
        )
        for circle in candidates
    )


    ranked = []

    for circle in candidates:

        topic_score = calculate_topic_score(
            user,
            circle,
        )

        activity_score = calculate_activity_score(
            circle,
            max_activity,
            engagement_by_circle,
        )

        freshness_score = calculate_freshness_score(
            circle,
            reference_time,
        )

        accessibility_score = calculate_accessibility_score(
            circle,
        )

        total_score = (
            topic_score
            + activity_score
            + freshness_score
            + accessibility_score
        )

        ranked.append({
            "circle": circle,
            "score": round(total_score, 2),
            "topic_score": round(topic_score, 2),
            "activity_score": round(activity_score, 2),
            "freshness_score": round(freshness_score, 2),
            "accessibility_score": round(
                accessibility_score, 2
            ),
        })


    ranked.sort(
        key=lambda item: (
            item["score"],
            -item["circle"].id,
        ),
        reverse=True,
    )

    selected = []
    deferred = []
    used_topics = set()

    for item in ranked:

        circle = item["circle"]
        topic_key = (
            circle.topic
            if circle.topic is not None
            else f"circle-{circle.id}"
        )

        if topic_key not in used_topics:
            selected.append(item)
            used_topics.add(topic_key)
        else:
            deferred.append(item)

        if len(selected) >= limit:
            break

    if len(selected) < limit:
        remaining = limit - len(selected)
        selected.extend(deferred[:remaining])

    return selected[:limit]
