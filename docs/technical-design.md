# Technical Design: Circle Recommendations API

## 1. Overview

The Circle Recommendations API helps members discover relevant, active, and accessible communities based on their interests and community activity.

The system uses a two-stage recommendation pipeline: eligibility filtering followed by weighted ranking. It is designed to support meaningful discovery while avoiding recommendations for Circles that members cannot join or that are no longer active.

The product goal is to help members find welcoming communities where they can build connections, share experiences, and support one another's growth.

## 2. Recommendation Pipeline

### Stage 1: Eligibility Filtering

Before scoring, the system removes Circles that do not meet the following conditions:

- The member is not already part of the Circle.
- The Circle is not private.
- The Circle is open for joining or accepts join requests.
- The Circle has available capacity.
- The Circle has recent activity within the defined 30-day window.

This ensures that ranking is performed only on communities that are relevant and realistically accessible to the member.

### Stage 2: Weighted Ranking

Each eligible Circle receives a score based on four components:

| Component | Weight | Rationale |
|---|---:|---|
| Topic relevance | 45% | Prioritizes alignment with member interests |
| Community activity | 25% | Favors communities with meaningful engagement |
| Freshness | 20% | Rewards recent community activity |
| Accessibility | 10% | Favors Circles that are easier to join |

The final score is calculated as:

**Final Score = Topic Score + Activity Score + Freshness Score + Accessibility Score**

Each component is normalized to its assigned maximum weight, resulting in a maximum recommendation score of 100.

### Topic Relevance

Topic relevance compares a member's interests with a Circle's primary and secondary topics.

A primary-topic match receives the highest score. Secondary-topic matches contribute proportionally based on the overlap between member interests and Circle topics.

### Community Activity

Activity scoring considers engagement signals such as:

- Posts
- Chat messages
- Reactions
- Comments
- Saves

These signals help distinguish active communities from those with limited participation.

### Freshness

Freshness scoring favors Circles with recent activity. The score decreases as the time since the latest activity increases.

This helps prevent inactive communities from receiving high rankings solely because of historical engagement.

### Accessibility

Accessibility scoring considers the Circle's join policy. Open Circles receive a higher score than Circles that require an approval request.

### Topic Diversity

After ranking, a diversity pass limits recommendations to one Circle per primary topic.

This reduces repetitive recommendations and gives members exposure to a broader range of communities. If fewer distinct topics are available than the requested recommendation limit, the API may return fewer results rather than reintroducing repeated topics.

## 3. Database Design

The application uses SQLite with SQLAlchemy ORM.

### Core Entities

- **Users:** Stores member information and profile attributes.
- **Circles:** Stores community details, capacity, format, join policy, and activity-related attributes.
- **Topics:** Stores available topics.
- **Memberships:** Tracks relationships between members and Circles.
- **Activity:** Stores engagement events associated with Circles.

Many-to-many relationships are represented through association tables:

- `user_interests` connects users with topics.
- `circle_topics` connects Circles with topics.

The Membership table uses a composite primary key on `(user_id, circle_id)` to prevent duplicate membership records.

### Indexing Strategy

The following indexes support common filtering and lookup operations:

| Index | Purpose |
|---|---|
| `idx_users_location` on `users.location` | Supports location-based member filtering when needed |
| `idx_users_industry` on `users.industry` | Supports industry-based member filtering when needed |
| `idx_circles_topic` on `circles.topic` | Supports topic-based Circle filtering |
| `idx_circles_format_join_policy` on `(format, join_policy)` | Supports filtering by Circle format and joining rules |
| `idx_memberships_circle` on `memberships.circle_id` | Supports membership lookups and Circle capacity checks |
| `idx_activity_circle_date` on `(circle_id, created_at)` | Supports recent activity queries and freshness calculations |

These indexes target fields used in filtering, relationship lookups, and activity calculations. Their effectiveness should be validated with query plans and representative production data as the dataset grows.

### Profile Attributes Not Used in Ranking

The dataset contains additional profile attributes, but not every available field is necessarily a reliable recommendation signal.

- **Job title:** Job titles can vary significantly in wording. Using them effectively would require normalization or a role taxonomy.
- **Industry:** Industry similarity may be useful, but it should not be assumed to indicate community interest without product evidence.
- **Location:** Location is more relevant for in-person communities and would benefit from normalized geographic matching.
- **Bio:** Free-text biographies may contain useful context, but reliable matching would require text processing and additional validation.
- **Profile completeness:** This describes how much profile information a member has provided, not how relevant a Circle is to that member.

These fields are intentionally excluded from the current scoring model to keep recommendations explainable and based on clearer signals.

## 4. API Design

The application uses FastAPI to expose a REST endpoint.

### Endpoint

`GET /api/users/{user_id}/recommendations?limit=10`

The endpoint returns ranked Circle recommendations for a member.

Each recommendation includes:

- Circle ID and details
- Overall recommendation score
- Individual score components
- Human-readable explanation

### Validation and Error Handling

- Returns `404` when the requested user does not exist.
- Returns `422` when request parameters fail validation.
- Restricts the recommendation limit to the supported range.

Pydantic schemas validate and structure API responses.

## 5. Technical Trade-offs and Future Improvements

### Current Implementation

- SQLite provides a lightweight database suitable for the assignment dataset.
- SQLAlchemy keeps database access structured and allows migration to another relational database.
- Weighted scoring is deterministic and explainable.
- Rule-based explanations avoid generating unsupported claims about why a Circle is recommended.
- A post-ranking diversity pass improves topic coverage.

### Production Considerations

For a larger production system, the following improvements would be valuable:

**Database and performance**
- Migrate to PostgreSQL for stronger production database capabilities and concurrent workloads.
- Precompute activity aggregates and member-topic features to reduce repeated calculations.
- Cache recommendation results where appropriate, with invalidation when interests, memberships, or Circle activity change.
- Use background jobs to refresh ranking features and recommendation candidates.

**Recommendation quality**
- Record recommendation impressions, clicks, joins, and subsequent engagement.
- Use these signals to evaluate whether recommendations lead to meaningful community participation.
- Consider learning-to-rank approaches once sufficient interaction data is available.

**Evaluation**
- Track Precision@K, Recall@K, and NDCG to evaluate ranking relevance.
- Run controlled experiments before changing scoring weights.
- Collect member feedback to understand whether recommendations feel relevant and welcoming.

**Fairness and quality**
- Monitor recommendation coverage across different member groups.
- Avoid allowing popularity or historical activity to dominate discovery.
- Ensure new and smaller Circles have opportunities to be discovered.
- Review recommendation quality regularly to identify stale or repetitive results.

## 6. Validation

The implementation includes automated tests covering:

- Cold-start recommendations
- Strong topic matches
- Duplicate-topic diversity
- Full and inactive Circle exclusion
- Existing membership exclusion
- Unknown users and invalid limits
- API response structure and error handling

The recommendation logic was also smoke-tested across the supplied dataset of 100 users to verify that each user received at least one recommendation.

The test suite automatically seeds the local database before execution.