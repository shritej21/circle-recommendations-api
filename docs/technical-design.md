# Technical Design: Circle Recommendations API

## 1. Overview

The Circle Recommendations API helps members discover relevant and active communities. It combines member interests, Circle activity, freshness, and joining accessibility to produce ranked recommendations with human-readable explanations.

The implementation uses Python, FastAPI, SQLAlchemy, and SQLite. The design prioritizes explainability, deterministic behavior, and a simple local development setup.

## 2. Recommendation Pipeline

The recommendation process has two stages:

**Eligibility filtering**

Before scoring, the system excludes:
- Circles the user has already joined.
- Private Circles.
- Full Circles, based on `member_count` and `max_members`.
- Inactive Circles with no activity in the last 30 days.

**Ranking and diversity**

Eligible Circles receive a weighted score out of 100:

| Signal | Weight |
|---|---:|
| Topic relevance | 45 |
| Community activity | 25 |
| Freshness | 20 |
| Accessibility | 10 |
| **Total** | **100** |

Topic relevance measures overlap between member interests and Circle topics. Activity considers recent posts, chat messages, reactions, comments, and saves. Freshness favors recently active Circles. Accessibility favors open-join Circles over request-to-join Circles.

After ranking, a diversity pass limits recommendations to one Circle per primary topic before filling remaining positions from deferred results. Ties are resolved deterministically using Circle IDs.

For reproducibility with the historical seed dataset, the reference time is derived from the latest Circle activity timestamp rather than the machine's current time.

## 3. Database Design

The database uses a normalized relational model:

- **Users:** Member profiles and profile attributes.
- **Circles:** Community metadata, format, capacity, join policy, and activity aggregates.
- **Topics:** Shared topic definitions.
- **Memberships:** User-to-Circle relationships, with a composite primary key.
- **User interests:** Many-to-many relationship between users and topics.
- **Circle topics:** Many-to-many relationship between Circles and topics.
- **Activity:** Circle activity records, including engagement counts and timestamps.

Foreign keys enforce relationships. Indexes support membership lookups, Circle eligibility and filtering, activity aggregation, and common profile queries.

## 4. API Design

`GET /api/users/{user_id}/recommendations?limit=10`

The endpoint returns Circle details, overall scores, score breakdowns, and member-facing explanations.

- `200`: Recommendations returned successfully.
- `404`: User does not exist.
- `422`: Invalid request parameters.

FastAPI handles routing and dependency injection, while Pydantic validates response structures.

## 5. Key Trade-offs and Limitations

- **Cold start:** Members without interests can still receive recommendations using activity, freshness, and accessibility signals.
- **Explainability:** Weighted signals make ranking decisions inspectable and easier to communicate.
- **Topic diversity:** Prevents repetitive recommendations but may suppress multiple highly relevant Circles under the same topic.
- **Activity weighting:** Engagement counts provide a lightweight popularity signal but do not fully represent content quality.
- **Historical data:** Using the latest seeded activity timestamp makes evaluation reproducible; a production system should use current time and scheduled activity updates.
- **Scalability:** SQLite is sufficient for this local assignment. A production deployment could use PostgreSQL, caching, precomputed features, and background ranking jobs.

## 6. Validation

The implementation includes 11 automated tests covering cold-start behavior, topic relevance, duplicate-topic diversity, full and inactive Circle filtering, existing memberships, invalid inputs, unknown users, and API responses.

The API was also manually verified through FastAPI Swagger documentation.