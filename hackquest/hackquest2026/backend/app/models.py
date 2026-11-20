"""Normalized schema for HACKQUEST CTF 2026."""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class RoundState(str, enum.Enum):
    LOCKED = "locked"
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"


class TeamStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISQUALIFIED = "disqualified"


class Organizer(Base):
    __tablename__ = "organizers"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(24), default="organizer", nullable=False)
    password_hash = Column(String(255), nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False, index=True)
    college = Column(String(180), nullable=False)
    department = Column(String(120), nullable=False)
    semester = Column(String(40), nullable=False)
    leader_name = Column(String(120), nullable=False)
    leader_email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    code = Column(String(16), unique=True, nullable=False, index=True)
    code_active = Column(Boolean, default=True, nullable=False)
    status = Column(Enum(TeamStatus), default=TeamStatus.PENDING, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    mobile = Column(String(32), nullable=False)
    is_leader = Column(Boolean, default=False, nullable=False)
    team = relationship("Team", back_populates="members")


class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    state = Column(Enum(RoundState), default=RoundState.LOCKED, nullable=False)
    opens_at = Column(DateTime(timezone=True), nullable=True)
    closes_at = Column(DateTime(timezone=True), nullable=True)
    paused_at = Column(DateTime(timezone=True), nullable=True)
    paused_seconds = Column(Integer, default=0, nullable=False)


class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True)
    round_number = Column(Integer, ForeignKey("rounds.number"), nullable=False, index=True)
    slug = Column(String(80), unique=True, nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(60), nullable=False)
    difficulty = Column(String(24), nullable=False)
    points = Column(Integer, nullable=False)
    flag = Column(String(160), nullable=False)
    flag_case_sensitive = Column(Boolean, default=True, nullable=False)
    flag_format = Column(String(120), default="HQCTF{...}", nullable=False)
    hint1 = Column(Text, nullable=False)
    hint2 = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    concept = Column(Text, nullable=False)
    attachment_name = Column(String(160), nullable=True)
    attachment_text = Column(Text, nullable=True)
    prerequisite_slug = Column(String(80), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_flag = Column(String(160), nullable=False)
    correct = Column(Boolean, nullable=False)
    points_awarded = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_submission_team_challenge", "team_id", "challenge_id"),
    )


class HintUse(Base):
    __tablename__ = "hint_uses"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    hint_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint("team_id", "challenge_id", "hint_index", name="uq_hint_use"),
    )


class Riddle(Base):
    __tablename__ = "riddles"
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(String(255), nullable=False)
    hint = Column(Text, nullable=False)
    category = Column(String(60), nullable=False)
    break_number = Column(Integer, nullable=False)
    reveal_enabled = Column(Boolean, default=False, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)


class Meme(Base):
    __tablename__ = "memes"
    id = Column(Integer, primary_key=True)
    title = Column(String(160), nullable=False)
    caption = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    break_number = Column(Integer, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True)
    title = Column(String(180), nullable=False)
    body = Column(Text, nullable=False)
    pinned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(Integer, nullable=False)
    action = Column(String(120), nullable=False)
    detail = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(80), primary_key=True)
    value = Column(Text, nullable=False)
