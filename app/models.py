
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    Table,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


user_interests = Table(
    "user_interests",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_id",
        Integer,
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


circle_topics = Table(
    "circle_topics",
    Base.metadata,
    Column(
        "circle_id",
        Integer,
        ForeignKey("circles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_id",
        Integer,
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    has_photo = Column(Boolean, default=False)
    bio = Column(Text, nullable=True)

    job_title = Column(String(150), nullable=True)
    company = Column(String(150), nullable=True)
    industry = Column(String(100), nullable=True)
    location = Column(String(150), nullable=True)

    joined_at = Column(DateTime, nullable=False)
    profile_completeness = Column(Float, default=0)

    interests = relationship(
        "Topic",
        secondary=user_interests,
        back_populates="interested_users",
    )

    memberships = relationship(
        "Membership",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Circle(Base):
    __tablename__ = "circles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    topic = Column(String(100), nullable=True)
    cover_image_url = Column(String(500), nullable=True)

    format = Column(String(50), nullable=False)
    access = Column(String(50), nullable=False)
    join_policy = Column(String(50), nullable=False)

    max_members = Column(Integer, nullable=True)
    member_count = Column(Integer, default=0)

    created_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, nullable=True)

    feed_posts_30d = Column(Integer, default=0)
    chat_messages_30d = Column(Integer, default=0)

    topics = relationship(
        "Topic",
        secondary=circle_topics,
        back_populates="circles",
    )

    memberships = relationship(
        "Membership",
        back_populates="circle",
        cascade="all, delete-orphan",
    )

    activities = relationship(
        "Activity",
        back_populates="circle",
        cascade="all, delete-orphan",
    )


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False)
    label = Column(String(150), nullable=False)
    domain = Column(String(100), nullable=True)

    interested_users = relationship(
        "User",
        secondary=user_interests,
        back_populates="interests",
    )

    circles = relationship(
        "Circle",
        secondary=circle_topics,
        back_populates="topics",
    )


class Membership(Base):
    __tablename__ = "memberships"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    circle_id = Column(
        Integer,
        ForeignKey("circles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role = Column(String(50), nullable=True)
    joined_at = Column(DateTime, nullable=False)

    user = relationship(
        "User",
        back_populates="memberships",
    )

    circle = relationship(
        "Circle",
        back_populates="memberships",
    )


class Activity(Base):
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True)

    circle_id = Column(
        Integer,
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=False,
    )

    author_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    body = Column(Text, nullable=True)

    reaction_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    save_count = Column(Integer, default=0)

    created_at = Column(DateTime, nullable=False)

    circle = relationship(
        "Circle",
        back_populates="activities",
    )


Index("idx_users_location", User.location)
Index("idx_users_industry", User.industry)

Index("idx_circles_topic", Circle.topic)
Index(
    "idx_circles_format_join_policy",
    Circle.format,
    Circle.join_policy,
)

Index("idx_memberships_circle", Membership.circle_id)

Index("idx_activity_circle_date", Activity.circle_id, Activity.created_at)
