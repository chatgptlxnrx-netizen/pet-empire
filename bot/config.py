"""
Configuration module for Pet Empire bot
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Bot Configuration
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Redis (optional)
    redis_url: str = Field(default="", alias="REDIS_URL")
    
    # Application
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Game Balance
    starting_coins: int = Field(default=1000, alias="STARTING_COINS")
    starting_slots: int = Field(default=5, alias="STARTING_SLOTS")
    max_pet_level: int = Field(default=100, alias="MAX_PET_LEVEL")
    daily_free_raids: int = Field(default=5, alias="DAILY_FREE_RAIDS")
    
    # Monetization
    stars_enabled: bool = Field(default=True, alias="STARS_ENABLED")
    ads_enabled: bool = Field(default=True, alias="ADS_ENABLED")
    
    # Features
    enable_trading: bool = Field(default=True, alias="ENABLE_TRADING")
    enable_achievements: bool = Field(default=True, alias="ENABLE_ACHIEVEMENTS")
    enable_battle_pass: bool = Field(default=True, alias="ENABLE_BATTLE_PASS")
    enable_leaderboards: bool = Field(default=True, alias="ENABLE_LEADERBOARDS")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse admin_ids if it's a string
        if isinstance(self.admin_ids, str):
            self.admin_ids = [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]


# Game constants
class GameConstants:
    """Game balance constants"""
    
    # Pet Rarities
    RARITIES = {
        "Common": {"color": "⚪️", "chance": 0.50, "base_income": 10, "base_power": 5},
        "Uncommon": {"color": "🟢", "chance": 0.30, "base_income": 25, "base_power": 12},
        "Rare": {"color": "🔵", "chance": 0.15, "base_income": 50, "base_power": 25},
        "Epic": {"color": "🟣", "chance": 0.04, "base_income": 150, "base_power": 60},
        "Legendary": {"color": "🟡", "chance": 0.009, "base_income": 500, "base_power": 150},
        "Mythical": {"color": "🌈", "chance": 0.001, "base_income": 2000, "base_power": 500}
    }
    
    # Pet Types
    PET_TYPES = [
        # Common pets
        "Cat", "Dog", "Hamster", "Parrot", "Rabbit",
        # Fantasy pets
        "Dragon", "Unicorn", "Phoenix", "Griffin", "Pegasus",
        # Meme pets
        "Doge", "Pepe", "Shiba", "Cheems", "Wojak",
        # Mythical pets
        "Cerberus", "Hydra", "Kraken", "Basilisk", "Manticore"
    ]
    
    # Mission Types
    MISSION_TYPES = {
        "quick": {
            "duration": 1800,  # 30 minutes
            "base_reward": 50,
            "exp_reward": 20,
            "fail_chance": 0.05
        },
        "medium": {
            "duration": 10800,  # 3 hours
            "base_reward": 200,
            "exp_reward": 80,
            "fail_chance": 0.15
        },
        "long": {
            "duration": 28800,  # 8 hours
            "base_reward": 800,
            "exp_reward": 300,
            "fail_chance": 0.25
        },
        "epic": {
            "duration": 43200,  # 12 hours
            "base_reward": 2000,
            "exp_reward": 800,
            "fail_chance": 0.30
        }
    }
    
    # Trap Types
    TRAP_TYPES = {
        "basic_wall": {"cost": 100, "defense_bonus": 10},
        "alarm": {"cost": 500, "defense_bonus": 15},
        "electric_fence": {"cost": 2000, "defense_bonus": 25},
        "laser_grid": {"cost": 10000, "defense_bonus": 50}
    }
    
    # Egg Costs
    EGG_COSTS = {
        "common": {"coins": 50, "stars": 0},
        "rare": {"coins": 0, "stars": 100},
        "epic": {"coins": 0, "stars": 250},
        "legendary": {"coins": 0, "stars": 500},
        "mythical": {"coins": 0, "stars": 1000}
    }
    
    # Level up requirements
    EXP_PER_LEVEL = 100  # Base EXP, increases by 10% each level
    EVOLUTION_LEVELS = [10, 25, 50, 75, 100]
    
    # Raid settings
    RAID_COOLDOWN = 21600  # 6 hours
    RAID_SHIELD_DURATION = 3600  # 1 hour after successful raid
    LOYALTY_STEAL_REDUCTION = 0.5  # 50% less chance if loyalty > 80
    
    # Trading
    TRADE_COMMISSION = 0.05  # 5%
    AUCTION_COMMISSION = 0.10  # 10%
    
    # Battle Pass
    BATTLE_PASS_LEVELS = 50
    BATTLE_PASS_COST = 400  # Stars


# Global settings instance
settings = Settings()
