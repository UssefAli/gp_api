from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import Depends
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from dotenv import load_dotenv
import os


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)



class Base(DeclarativeBase):
    pass



class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"


    role = Column(String, nullable=False, default="user")

    # Common fields
    name = Column(String)
    phone = Column(String)
    canceled_count = Column(Integer, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Normal user fields
    user_lat = Column(Numeric(9, 6))
    user_lng = Column(Numeric(9, 6))
    car_type = Column(String)
    car_model = Column(String)

    # Mechanic fields
    workshop_name = Column(String)
    experience_years = Column(Integer)
    workshop_lat = Column(Numeric(9, 6))
    workshop_lng = Column(Numeric(9, 6))
    total_jobs = Column(Integer)
    avg_rating = Column(Float)
    is_available = Column(Boolean, server_default="false")
    review_count = Column(Integer)
    test_column = Column(String)
    # Relationships
    service_requests = relationship(
        "ServiceRequest",
        back_populates="user",
        foreign_keys="ServiceRequest.user_id",
    )

    mechanic_requests = relationship(
        "ServiceRequest",
        back_populates="mechanic",
        foreign_keys="ServiceRequest.mechanic_id",
    )

    ratings_given = relationship(
        "Rating",
        back_populates="user",
        foreign_keys="Rating.user_id",
    )

    ratings_received = relationship(
        "Rating",
        back_populates="mechanic",
        foreign_keys="Rating.mechanic_id",
    )

    skills = relationship(
        "MechanicSkill",
        back_populates="mechanic",
        cascade="all, delete-orphan",
    )




class ServiceRequest(Base):
    __tablename__ = "service_requests"

    request_id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    mechanic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    request_type = Column(String, nullable=False)
    status = Column(String, nullable=False)

    user_lat = Column(Numeric(9, 6))
    user_lng = Column(Numeric(9, 6))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    completed_at = Column(DateTime(timezone=True))

    user = relationship(
        "User",
        back_populates="service_requests",
        foreign_keys=[user_id],
    )

    mechanic = relationship(
        "User",
        back_populates="mechanic_requests",
        foreign_keys=[mechanic_id],
    )

    tracking = relationship(
        "LocationTracking",
        back_populates="request",
        cascade="all, delete-orphan",
    )

    rating = relationship(
        "Rating",
        back_populates="request",
        uselist=False,
        cascade="all, delete-orphan",
    )



class LocationTracking(Base):
    __tablename__ = "location_tracking"

    track_id = Column(Integer, primary_key=True, autoincrement=True)

    request_id = Column(
        Integer,
        ForeignKey("service_requests.request_id", ondelete="CASCADE"),
        nullable=False,
    )

    mechanic_lat = Column(Numeric(9, 6))
    mechanic_lng = Column(Numeric(9, 6))

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    request = relationship(
        "ServiceRequest",
        back_populates="tracking",
    )



class Rating(Base):
    __tablename__ = "ratings"

    rating_id = Column(Integer, primary_key=True, autoincrement=True)

    request_id = Column(
        Integer,
        ForeignKey("service_requests.request_id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    mechanic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    rating = Column(Integer, nullable=False)
    feedback_text = Column(Text)
    applied_reward = Column(Float)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="ratings_given",
        foreign_keys=[user_id],
    )

    mechanic = relationship(
        "User",
        back_populates="ratings_received",
        foreign_keys=[mechanic_id],
    )

    request = relationship(
        "ServiceRequest",
        back_populates="rating",
    )



class Skill(Base):
    __tablename__ = "skills"

    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String, unique=True, nullable=False)

    mechanics = relationship(
        "MechanicSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )


class MechanicSkill(Base):
    __tablename__ = "mechanic_skills"

    mechanic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    skill_id = Column(
        Integer,
        ForeignKey("skills.skill_id", ondelete="CASCADE"),
        primary_key=True,
    )

    mechanic = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="mechanics")




class RecommendationWeights(Base):
    __tablename__ = "recommendation_weights"

    id = Column(Integer, primary_key=True)

    rating_weight = Column(Float, nullable=False, default=0.6)
    distance_weight = Column(Float, nullable=False, default=0.4)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )



async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
):
    yield SQLAlchemyUserDatabase(session, User)


async def get_request_db(
    session: AsyncSession = Depends(get_async_session),
):
    yield SQLAlchemyUserDatabase(session, ServiceRequest)



