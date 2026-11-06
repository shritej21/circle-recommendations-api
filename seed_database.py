
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import Base, engine
from app.models import (
    User,
    Circle,
    Topic,
    Membership,
    Activity,
)

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename):
    """Load records from a JSON dataset."""
    path = DATA_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_datetime(value):
    """Convert ISO 8601 timestamps into UTC-naive datetimes."""
    if value is None:
        return None

    parsed = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    return parsed.replace(tzinfo=None)


def seed_database():
    # Load all source datasets.
    users_data = load_json("users.json")
    circles_data = load_json("circles.json")
    memberships_data = load_json("memberships.json")
    topics_data = load_json("topics.json")
    activity_data = load_json("activity.json")

    # Rebuild the local database for a deterministic seed.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        try:
            # 1. Insert topics.
            topics = [
                Topic(
                    id=item["id"],
                    slug=item["slug"],
                    label=item["label"],
                    domain=item.get("domain"),
                )
                for item in topics_data
            ]

            session.add_all(topics)
            session.flush()

            topic_by_slug = {
                topic.slug: topic for topic in topics
            }

            # 2. Insert users and their interests.
            users = []

            for item in users_data:
                user = User(
                    id=item["id"],
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    has_photo=item["has_photo"],
                    bio=item.get("bio"),
                    job_title=item.get("job_title"),
                    company=item.get("company"),
                    industry=item.get("industry"),
                    location=item.get("location"),
                    joined_at=parse_datetime(item["joined_at"]),
                    profile_completeness=item.get(
                        "profile_completeness", 0
                    ),
                )

                user.interests = [
                    topic_by_slug[slug]
                    for slug in item["topic_interests"]
                ]

                users.append(user)

            session.add_all(users)

            # 3. Insert Circles and their topics.
            circles = []

            for item in circles_data:
                circle = Circle(
                    id=item["id"],
                    name=item["name"],
                    slug=item["slug"],
                    description=item.get("description"),
                    topic=item.get("topic"),
                    cover_image_url=item.get("cover_image_url"),
                    format=item["format"],
                    access=item["access"],
                    join_policy=item["join_policy"],
                    max_members=item.get("max_members"),
                    member_count=item["member_count"],
                    created_at=parse_datetime(item["created_at"]),
                    last_activity_at=parse_datetime(
                        item.get("last_activity_at")
                    ),
                    feed_posts_30d=item["feed_posts_30d"],
                    chat_messages_30d=item["chat_messages_30d"],
                )

                # Include the primary topic and all additional tags.
                circle_slugs = set(item.get("tags") or [])

                if item.get("topic"):
                    circle_slugs.add(item["topic"])

                circle.topics = [
                    topic_by_slug[slug]
                    for slug in sorted(circle_slugs)
                ]

                circles.append(circle)

            session.add_all(circles)

            # Ensure parent records exist before dependent records.
            session.flush()

            # 4. Insert memberships.
            memberships = [
                Membership(
                    user_id=item["user_id"],
                    circle_id=item["circle_id"],
                    role=item.get("role"),
                    joined_at=parse_datetime(item["joined_at"]),
                )
                for item in memberships_data
            ]

            session.add_all(memberships)

            # 5. Insert activity records.
            activities = [
                Activity(
                    id=item["id"],
                    circle_id=item["circle_id"],
                    author_user_id=item.get("author_user_id"),
                    body=item.get("body"),
                    reaction_count=item.get("reaction_count", 0),
                    comment_count=item.get("comment_count", 0),
                    save_count=item.get("save_count", 0),
                    created_at=parse_datetime(item["created_at"]),
                )
                for item in activity_data
            ]

            session.add_all(activities)

            # Commit everything together.
            session.commit()

            print("\nDatabase seeding completed successfully!")
            print("------------------------------------------")
            print(f"Users:       {len(users)}")
            print(f"Circles:     {len(circles)}")
            print(f"Topics:      {len(topics)}")
            print(f"Memberships: {len(memberships)}")
            print(f"Activities:  {len(activities)}")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    seed_database()
