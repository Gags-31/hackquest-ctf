"""SQLAlchemy models for HackQuest CTF 2026."""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer,
    String, Text, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class ScoringMode(str, enum.Enum):
    TIER = "tier"          # max 4200
    NORMALIZED = "normalized"  # max 3499/3500


class RoundState(str, enum.Enum):
    LOCKED = "locked"
    OPEN = "open"
    CLOSED = "closed"


class TeamStatus(str, enum.Enum):
    ACTIVE = "active"
    VERIFIED = "verified"
    DISQUALIFIED = "disqualified"


class Organizer(Base):
    """One of two independent organizer accounts."""
    __tablename__ = "organizers"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    # role: admin (full control) or moderator (content + proctoring review)
    role = Column(String(20), default="moderator", nullable=False)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    last_login_at = Column(DateTime(timezone=True))

    @property
    def is_admin(self):
        return self.role == "admin"


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    team_code = Column(String(12), unique=True, nullable=False, index=True)
    leader_name = Column(String(120), nullable=False)
    leader_email = Column(String(255), nullable=False, index=True)
    college = Column(String(160), default="")
    branch = Column(String(80), default="")
    semester = Column(String(40), default="")
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(TeamStatus), default=TeamStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    members = relationship("TeamMember", back_populates="team",
                           cascade="all, delete-orphan", lazy="selectin")
    submissions = relationship("Submission", back_populates="team", lazy="selectin")
    unlocks = relationship("RoundUnlock", back_populates="team", lazy="selectin")

    @property
    def member_count(self):
        return 1 + len(self.members)

    @property
    def is_disqualified(self):
        return self.status == TeamStatus.DISQUALIFIED


class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    branch = Column(String(80), default="")
    semester = Column(String(40), default="")
    college = Column(String(160), default="")
    is_leader = Column(Boolean, default=False)
    team = relationship("Team", back_populates="members")


class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, nullable=False)
    slug = Column(String(40), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    blurb = Column(Text, default="")
    state = Column(Enum(RoundState), default=RoundState.LOCKED, nullable=False)
    unlock_code = Column(String(255), nullable=False)   # server-generated only
    opens_at = Column(DateTime(timezone=True))
    closes_at = Column(DateTime(timezone=True))
    explanation = Column(Text, default="")              # shown only after close

    challenges = relationship("Challenge", back_populates="round",
                              cascade="all, delete-orphan", lazy="selectin",
                              order_by="Challenge.order_index")


class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("rounds.id", ondelete="CASCADE"), index=True)
    key = Column(String(40), unique=True, nullable=False, index=True)
    order_index = Column(Integer, default=0)
    title = Column(String(120), nullable=False)
    category = Column(String(60), default="General")
    difficulty = Column(String(20), default="Easy")
    description = Column(Text, nullable=False)
    answer_format = Column(String(160), default="")
    initial_clue = Column(Text, default="")
    hint1 = Column(Text, default="")
    hint2 = Column(Text, default="")
    hint3 = Column(Text, default="")
    # PRIVATE. Never serialised to participants.
    answer_key = Column(String(255), nullable=False)
    segment = Column(String(64), nullable=False)      # contribution to unlock code
    explanation = Column(Text, default="")            # shown after round closes
    is_code_challenge = Column(Boolean, default=False)
    hidden_tests = Column(Text, default="")           # JSON, never exposed pre-competition
    round = relationship("Round", back_populates="challenges")


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    challenge_key = Column(String(40), nullable=False, index=True)
    round_number = Column(Integer, nullable=False, index=True)
    answer = Column(Text, default="")
    normalized = Column(Text, default="")
    correct = Column(Boolean, default=False, nullable=False)
    points_awarded = Column(Integer, default=0)
    hint_used = Column(Integer, default=0)
    attempt_number = Column(Integer, default=1)
    at = Column(DateTime(timezone=True), default=utcnow, index=True)
    team = relationship("Team", back_populates="submissions")

    __table_args__ = (
        UniqueConstraint("team_id", "challenge_key", name="uq_team_challenge"),
        Index("ix_team_correct", "team_id", "correct"),
    )


class RoundUnlock(Base):
    __tablename__ = "round_unlocks"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    round_number = Column(Integer, nullable=False)
    code_used = Column(String(255), default="")
    unlocked_at = Column(DateTime(timezone=True), default=utcnow)
    team = relationship("Team", back_populates="unlocks")

    __table_args__ = (UniqueConstraint("team_id", "round_number", name="uq_team_round"),)


class HintUse(Base):
    __tablename__ = "hint_uses"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    challenge_key = Column(String(40), nullable=False)
    hint_number = Column(Integer, nullable=False)
    at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (UniqueConstraint("team_id", "challenge_key", "hint_number",
                                      name="uq_team_challenge_hint"),)


class Violation(Base):
    __tablename__ = "violations"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    kind = Column(String(60), nullable=False)
    detail = Column(String(255), default="")
    at = Column(DateTime(timezone=True), default=utcnow, index=True)
    reviewed = Column(Boolean, default=False)
    forgiven = Column(Boolean, default=False)
    review_note = Column(String(255), default="")
    reviewed_by = Column(String(64), default="")

    team = relationship("Team")


class AuditLog(Base):
    """Append-only. The application exposes no UPDATE or DELETE for this table."""
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    actor = Column(String(64), nullable=False, index=True)
    action = Column(String(80), nullable=False, index=True)
    target = Column(String(160), default="")
    detail = Column(Text, default="")
    at = Column(DateTime(timezone=True), default=utcnow, index=True)
    ip = Column(String(64), default="")

    __table_args__ = (Index("ix_audit_actor_action", "actor", "action"),)


class AppSetting(Base):
    __tablename__ = "app_settings"
    key = Column(String(60), primary_key=True)
    value = Column(String(400), default="")

    @property
    def as_float(self) -> float:
        try:
            return float(self.value)
        except (TypeError, ValueError):
            return 0.0

    @property
    def as_int(self) -> int:
        try:
            return int(float(self.value))
        except (TypeError, ValueError):
            return 0

    @property
    def as_bool(self) -> bool:
        return str(self.value).lower() in ("1", "true", "yes", "on")