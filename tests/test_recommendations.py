
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.services.recommendation import recommend_circles


@pytest.fixture(scope="session", autouse=True)
def seed_test_database():
    """Seed the database once before running the test suite."""
    from seed_database import seed_database

    seed_database()


client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_circle_ids(results):
    return [item["circle"].id for item in results]


def test_cold_start_user_receives_recommendations(db):
    results = recommend_circles(db, user_id=42, limit=10)

    assert len(results) > 0
    assert len(results) <= 10

    ids = get_circle_ids(results)
    assert len(ids) == len(set(ids))


def test_obvious_topic_matches_rank_well(db):
    results = recommend_circles(db, user_id=7, limit=10)

    ids = get_circle_ids(results)

    assert 6 in ids
    assert results[0]["topic_score"] == 45.0


def test_duplicate_topics_are_diversified(db):
    results = recommend_circles(db, user_id=15, limit=20)

    ids = get_circle_ids(results)

    negotiation_ids = {10, 11, 12}
    returned_duplicates = negotiation_ids.intersection(ids)

    # At most one Circle from this duplicate-topic group should appear.
    assert len(returned_duplicates) <= 1

    # Recommendations should not contain duplicate Circle IDs.
    assert len(ids) == len(set(ids))


def test_full_and_inactive_circles_are_excluded(db):
    results = recommend_circles(db, user_id=23, limit=10)

    ids = get_circle_ids(results)

    assert 20 not in ids
    assert 21 not in ids
    assert ids[0] == 22


def test_existing_memberships_are_excluded(db):
    results = recommend_circles(db, user_id=7, limit=10)

    ids = get_circle_ids(results)

    assert 4 not in ids


def test_unknown_user_raises_error(db):
    with pytest.raises(ValueError, match="not found"):
        recommend_circles(db, user_id=9999)


def test_invalid_limit_raises_error(db):
    with pytest.raises(ValueError, match="greater than zero"):
        recommend_circles(db, user_id=7, limit=0)


def test_api_returns_recommendations():
    response = client.get(
        "/api/users/42/recommendations?limit=10"
    )

    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == 42
    assert len(data["recommendations"]) > 0

    first = data["recommendations"][0]

    assert "circle_id" in first
    assert "name" in first
    assert "score" in first
    assert "score_breakdown" in first
    assert "explanation" in first


def test_api_returns_topic_match():
    response = client.get(
        "/api/users/7/recommendations?limit=5"
    )

    assert response.status_code == 200

    recommendations = response.json()["recommendations"]

    assert recommendations[0]["score_breakdown"]["topic"] == 45
    assert any(
        item["circle_id"] == 6
        for item in recommendations
    )


def test_api_returns_404_for_unknown_user():
    response = client.get(
        "/api/users/9999/recommendations"
    )

    assert response.status_code == 404


def test_api_rejects_invalid_limit():
    response = client.get(
        "/api/users/42/recommendations?limit=0"
    )

    assert response.status_code == 422
