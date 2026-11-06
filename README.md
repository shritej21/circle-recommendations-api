# Circle Recommendations API

A recommendation API that helps members discover relevant, active Circles based on their interests and community activity.

## Features

- Personalized Circle recommendations using member interests and Circle topics.
- Activity-based ranking using posts, chat messages, reactions, comments, and saves.
- Freshness scoring to favor recently active communities.
- Eligibility filtering for existing memberships, private Circles, full Circles, and inactive Circles.
- Topic diversity to avoid recommending too many Circles around the same topic.
- Human-readable explanations and score breakdowns.
- REST API built with FastAPI and SQLite.

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Pytest

## Project Structure

```text
app/
  main.py
  database.py
  models.py
  schemas.py
  routers/
    recommendations.py
  services/
    recommendation.py
    explanations.py
data/
tests/
  test_recommendations.py
docs/
  technical-design.md
requirements.txt
seed_database.py
AI_NOTES.md
README.md
```

## Setup

Clone the repository:

```bash
git clone https://github.com/shritej21/circle-recommendations-api.git
cd circle-recommendations-api
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Load the Dataset

Seed the local SQLite database:

```bash
python seed_database.py
```

The seed script loads the supplied users, Circles, topics, memberships, and activity data.

**Note:** Running the seed script drops and recreates the local database, replacing its existing contents.

## Run the API

Start the development server:

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

- Health check: http://127.0.0.1:8000/
- Interactive API documentation: http://127.0.0.1:8000/docs

## API Usage

### Get Circle Recommendations

```http
GET /api/users/{user_id}/recommendations?limit=10
```

Example:

```bash
curl "http://127.0.0.1:8000/api/users/7/recommendations?limit=5"
```

The response includes:

- Circle details
- Overall recommendation score
- Individual score components
- A human-readable explanation

The `limit` parameter accepts values from 1 to 20 and defaults to 10.

### Error Handling

- `404`: User does not exist.
- `422`: Invalid request parameters.

## Recommendation Approach

Recommendations are generated in two stages:

1. **Eligibility filtering:** Excludes existing memberships, private Circles, full Circles, and inactive Circles.
2. **Ranking:** Scores eligible Circles using topic relevance, community activity, freshness, and accessibility. A diversity pass limits repeated primary topics.

The ranking methodology, database design, and implementation trade-offs are explained in [Technical Design](docs/technical-design.md).

## Run Tests

Run the automated test suite:

```bash
python -m pytest -v
```

The test suite automatically seeds the database once per test session. No manual database seeding is required before running tests.

**Note:** The test setup recreates the local SQLite database. Any existing local database contents will be replaced.

The tests cover:

- Cold-start recommendations
- Topic relevance and ranking
- Duplicate-topic diversity
- Full and inactive Circle exclusion
- Existing membership exclusion
- Unknown users and invalid limits
- API response structure and error handling

## Design Documentation

See [Technical Design](docs/technical-design.md) for the database schema, ranking methodology, design decisions, and trade-offs.

See [AI Usage Notes](AI_NOTES.md) for transparency about the use of AI assistance during development.