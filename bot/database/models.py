"""
Database models for Pet Empire
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, Integer, String, Float, 
    DateTime, ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Game Progress
    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)
    coins: Mapped[int] = mapped_column(BigInteger, default=1000)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    
    # Slots & Capacity
    pet_slots: Mapped[int] = mapped_column(Integer, default=5)
    max_defenders: Mapped[int] = mapped_column(Integer, default=3)
    
    # Battle Pass
    battle_pass_level: Mapped[int] = mapped_column(Integer, default=0)
    battle_pass_exp: Mapped[int] = mapped_column(Integer, default=0)
    has_premium_pass: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Raid Stats
    raids_won: Mapped[int] = mapped_column(Integer, default=0)
    raids_lost: Mapped[int] = mapped_column(Integer, default=0)
    defenses_won: Mapped[int] = mapped_column(Integer, default=0)
    defenses_lost: Mapped[int] = mapped_column(Integer, default=0)
    free_raids_today: Mapped[int] = mapped_column(Integer, default=5)
    last_raid_reset: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    raid_shield_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Traps (JSON: {trap_type: level})
    traps: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # VIP
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    vip_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Tutorial
    tutorial_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    pets: Mapped[list["Pet"]] = relationship(
        "Pet", 
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    missions: Mapped[list["Mission"]] = relationship(
        "Mission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    achievements_progress: Mapped[list["AchievementProgress"]] = relationship(
        "AchievementProgress",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_level", "level"),
        Index("idx_user_coins", "coins"),
        Index("idx_user_last_active", "last_active"),
    )
    
    def __repr__(self):
        return f"<User {self.user_id} ({self.username})>"


class Pet(Base):
    """Pet model"""
    __tablename__ = "pets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("users.user_id", ondelete="CASCADE")
    )
    
    # Pet Info
    name: Mapped[str] = mapped_column(String(100))
    pet_type: Mapped[str] = mapped_column(String(50))
    rarity: Mapped[str] = mapped_column(String(20))
    emoji: Mapped[str] = mapped_column(String(10), default="🐾")
    
    # Stats
    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)
    power: Mapped[int] = mapped_column(Integer)
    income_per_hour: Mapped[int] = mapped_column(Integer)
    stamina: Mapped[int] = mapped_column(Integer, default=100)
    loyalty: Mapped[int] = mapped_column(Integer, default=50)
    
    # Status
    is_on_mission: Mapped[bool] = mapped_column(Boolean, default=False)
    is_defending: Mapped[bool] = mapped_column(Boolean, default=False)
    fatigue_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Special
    evolution_stage: Mapped[int] = mapped_column(Integer, default=0)
    is_shiny: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    obtained_from: Mapped[str] = mapped_column(String(50), default="egg")  # egg, raid, trade, reward
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="pets")
    mission: Mapped[Optional["Mission"]] = relationship(
        "Mission",
        back_populates="pet",
        uselist=False
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_pet_owner", "owner_id"),
        Index("idx_pet_rarity", "rarity"),
        Index("idx_pet_level", "level"),
        Index("idx_pet_mission", "is_on_mission"),
    )
    
    @property
    def total_value(self) -> int:
        """Calculate pet's total value"""
        base_value = {
            "Common": 100,
            "Uncommon": 300,
            "Rare": 800,
            "Epic": 2500,
            "Legendary": 10000,
            "Mythical": 50000
        }
        return int(base_value.get(self.rarity, 100) * (1 + self.level * 0.1))
    
    def __repr__(self):
        return f"<Pet {self.name} ({self.rarity} {self.pet_type})>"


class Mission(Base):
    """Mission model"""
    __tablename__ = "missions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE")
    )
    pet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pets.id", ondelete="CASCADE")
    )
    
    # Mission Details
    mission_type: Mapped[str] = mapped_column(String(50))
    mission_name: Mapped[str] = mapped_column(String(200))
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    complete_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Rewards
    reward_coins: Mapped[int] = mapped_column(Integer)
    reward_exp: Mapped[int] = mapped_column(Integer)
    bonus_item: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="active"
    )  # active, completed, failed, collected
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="missions")
    pet: Mapped["Pet"] = relationship("Pet", back_populates="mission")
    
    # Indexes
    __table_args__ = (
        Index("idx_mission_user", "user_id"),
        Index("idx_mission_status", "status"),
        Index("idx_mission_complete", "complete_at"),
    )
    
    def __repr__(self):
        return f"<Mission {self.mission_name} ({self.status})>"


class Raid(Base):
    """Raid history model"""
    __tablename__ = "raids"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attacker_id: Mapped[int] = mapped_column(BigInteger)
    defender_id: Mapped[int] = mapped_column(BigInteger)
    
    # Battle Stats
    attacker_power: Mapped[int] = mapped_column(Integer)
    defender_power: Mapped[int] = mapped_column(Integer)
    
    # Result
    result: Mapped[str] = mapped_column(String(20))  # win, lose
    stolen_pet_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_raid_attacker", "attacker_id"),
        Index("idx_raid_defender", "defender_id"),
        Index("idx_raid_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<Raid {self.attacker_id} vs {self.defender_id} ({self.result})>"


class Achievement(Base):
    """Achievement definitions"""
    __tablename__ = "achievements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(10))
    
    # Requirements
    requirement_type: Mapped[str] = mapped_column(String(50))
    requirement_value: Mapped[int] = mapped_column(Integer)
    
    # Rewards
    reward_coins: Mapped[int] = mapped_column(Integer, default=0)
    reward_stars: Mapped[int] = mapped_column(Integer, default=0)
    reward_item: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Metadata
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[str] = mapped_column(String(50))
    
    def __repr__(self):
        return f"<Achievement {self.name}>"


class AchievementProgress(Base):
    """User achievement progress"""
    __tablename__ = "achievement_progress"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE")
    )
    achievement_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("achievements.id", ondelete="CASCADE")
    )
    
    # Progress
    current_value: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements_progress")
    
    # Indexes
    __table_args__ = (
        Index("idx_achievement_user", "user_id"),
        Index("idx_achievement_completed", "completed"),
    )
    
    def __repr__(self):
        return f"<AchievementProgress user={self.user_id} achievement={self.achievement_id}>"


class Trade(Base):
    """Trade history"""
    __tablename__ = "trades"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Parties
    sender_id: Mapped[int] = mapped_column(BigInteger)
    receiver_id: Mapped[int] = mapped_column(BigInteger)
    
    # Offer
    sender_pets: Mapped[list] = mapped_column(JSON)  # List of pet IDs
    receiver_pets: Mapped[list] = mapped_column(JSON)  # List of pet IDs
    sender_coins: Mapped[int] = mapped_column(Integer, default=0)
    receiver_coins: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, declined, expired
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Indexes
    __table_args__ = (
        Index("idx_trade_sender", "sender_id"),
        Index("idx_trade_receiver", "receiver_id"),
        Index("idx_trade_status", "status"),
    )
    
    def __repr__(self):
        return f"<Trade {self.sender_id} -> {self.receiver_id} ({self.status})>"
