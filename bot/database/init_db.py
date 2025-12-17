"""
Database initialization script
"""
import asyncio
from sqlalchemy import select
from loguru import logger

from bot.config import settings
from bot.database.db import db
from bot.database.models import Achievement


# Achievement definitions
ACHIEVEMENTS = [
    # Collection Achievements
    {
        "key": "first_pet",
        "name": "🐣 First Step",
        "description": "Получи своего первого питомца",
        "icon": "🐣",
        "requirement_type": "pets_owned",
        "requirement_value": 1,
        "reward_coins": 100,
        "reward_stars": 0,
        "category": "collection",
        "is_hidden": False
    },
    {
        "key": "collector_5",
        "name": "🎯 Collector",
        "description": "Собери 5 разных питомцев",
        "icon": "🎯",
        "requirement_type": "pets_owned",
        "requirement_value": 5,
        "reward_coins": 500,
        "reward_stars": 0,
        "category": "collection",
        "is_hidden": False
    },
    {
        "key": "collector_10",
        "name": "🏆 Master Collector",
        "description": "Собери 10 разных питомцев",
        "icon": "🏆",
        "requirement_type": "pets_owned",
        "requirement_value": 10,
        "reward_coins": 2000,
        "reward_stars": 50,
        "category": "collection",
        "is_hidden": False
    },
    {
        "key": "rare_collector",
        "name": "💎 Rare Hunter",
        "description": "Получи питомца редкости Rare или выше",
        "icon": "💎",
        "requirement_type": "rare_pet_owned",
        "requirement_value": 1,
        "reward_coins": 1000,
        "reward_stars": 25,
        "category": "collection",
        "is_hidden": False
    },
    {
        "key": "legendary_owner",
        "name": "⭐ Legend",
        "description": "Получи легендарного питомца",
        "icon": "⭐",
        "requirement_type": "legendary_pet_owned",
        "requirement_value": 1,
        "reward_coins": 5000,
        "reward_stars": 100,
        "category": "collection",
        "is_hidden": False
    },
    
    # Mission Achievements
    {
        "key": "first_mission",
        "name": "🚀 First Mission",
        "description": "Отправь питомца на первую миссию",
        "icon": "🚀",
        "requirement_type": "missions_completed",
        "requirement_value": 1,
        "reward_coins": 100,
        "reward_stars": 0,
        "category": "missions",
        "is_hidden": False
    },
    {
        "key": "mission_veteran_10",
        "name": "🎖️ Veteran",
        "description": "Завершите 10 миссий",
        "icon": "🎖️",
        "requirement_type": "missions_completed",
        "requirement_value": 10,
        "reward_coins": 500,
        "reward_stars": 0,
        "category": "missions",
        "is_hidden": False
    },
    {
        "key": "mission_expert_50",
        "name": "⚔️ Expert",
        "description": "Завершите 50 миссий",
        "icon": "⚔️",
        "requirement_type": "missions_completed",
        "requirement_value": 50,
        "reward_coins": 3000,
        "reward_stars": 50,
        "category": "missions",
        "is_hidden": False
    },
    {
        "key": "mission_master_100",
        "name": "👑 Mission Master",
        "description": "Завершите 100 миссий",
        "icon": "👑",
        "requirement_type": "missions_completed",
        "requirement_value": 100,
        "reward_coins": 10000,
        "reward_stars": 150,
        "category": "missions",
        "is_hidden": False
    },
    
    # Raid Achievements
    {
        "key": "first_raid",
        "name": "⚡ First Raid",
        "description": "Проведи свой первый рейд",
        "icon": "⚡",
        "requirement_type": "raids_attempted",
        "requirement_value": 1,
        "reward_coins": 200,
        "reward_stars": 0,
        "category": "raids",
        "is_hidden": False
    },
    {
        "key": "raid_winner_10",
        "name": "🗡️ Raider",
        "description": "Выиграй 10 рейдов",
        "icon": "🗡️",
        "requirement_type": "raids_won",
        "requirement_value": 10,
        "reward_coins": 1000,
        "reward_stars": 25,
        "category": "raids",
        "is_hidden": False
    },
    {
        "key": "raid_master_50",
        "name": "💀 Raid Master",
        "description": "Выиграй 50 рейдов",
        "icon": "💀",
        "requirement_type": "raids_won",
        "requirement_value": 50,
        "reward_coins": 5000,
        "reward_stars": 100,
        "category": "raids",
        "is_hidden": False
    },
    {
        "key": "defender_10",
        "name": "🛡️ Defender",
        "description": "Успешно защитись 10 раз",
        "icon": "🛡️",
        "requirement_type": "defenses_won",
        "requirement_value": 10,
        "reward_coins": 1000,
        "reward_stars": 25,
        "category": "raids",
        "is_hidden": False
    },
    {
        "key": "fortress_50",
        "name": "🏰 Fortress",
        "description": "Успешно защитись 50 раз",
        "icon": "🏰",
        "requirement_type": "defenses_won",
        "requirement_value": 50,
        "reward_coins": 5000,
        "reward_stars": 100,
        "category": "raids",
        "is_hidden": False
    },
    
    # Wealth Achievements
    {
        "key": "rich_10k",
        "name": "💰 Getting Rich",
        "description": "Накопи 10,000 монет",
        "icon": "💰",
        "requirement_type": "coins_earned",
        "requirement_value": 10000,
        "reward_coins": 500,
        "reward_stars": 0,
        "category": "wealth",
        "is_hidden": False
    },
    {
        "key": "rich_100k",
        "name": "💎 Wealthy",
        "description": "Накопи 100,000 монет",
        "icon": "💎",
        "requirement_type": "coins_earned",
        "requirement_value": 100000,
        "reward_coins": 5000,
        "reward_stars": 100,
        "category": "wealth",
        "is_hidden": False
    },
    {
        "key": "millionaire",
        "name": "🌟 Millionaire",
        "description": "Накопи 1,000,000 монет",
        "icon": "🌟",
        "requirement_type": "coins_earned",
        "requirement_value": 1000000,
        "reward_coins": 50000,
        "reward_stars": 500,
        "category": "wealth",
        "is_hidden": False
    },
    
    # Level Achievements
    {
        "key": "level_10",
        "name": "📈 Rising Star",
        "description": "Достигни 10 уровня",
        "icon": "📈",
        "requirement_type": "level_reached",
        "requirement_value": 10,
        "reward_coins": 1000,
        "reward_stars": 25,
        "category": "progression",
        "is_hidden": False
    },
    {
        "key": "level_25",
        "name": "🌠 Pro Player",
        "description": "Достигни 25 уровня",
        "icon": "🌠",
        "requirement_type": "level_reached",
        "requirement_value": 25,
        "reward_coins": 5000,
        "reward_stars": 100,
        "category": "progression",
        "is_hidden": False
    },
    {
        "key": "level_50",
        "name": "👑 Elite",
        "description": "Достигни 50 уровня",
        "icon": "👑",
        "requirement_type": "level_reached",
        "requirement_value": 50,
        "reward_coins": 20000,
        "reward_stars": 250,
        "category": "progression",
        "is_hidden": False
    },
    
    # Special Achievements
    {
        "key": "max_level_pet",
        "name": "🔥 Perfect Training",
        "description": "Прокачай питомца до 100 уровня",
        "icon": "🔥",
        "requirement_type": "max_level_pet",
        "requirement_value": 1,
        "reward_coins": 10000,
        "reward_stars": 200,
        "reward_item": "mythical_egg",
        "category": "special",
        "is_hidden": False
    },
    {
        "key": "trader",
        "name": "🤝 Trader",
        "description": "Совершите 10 успешных обменов",
        "icon": "🤝",
        "requirement_type": "trades_completed",
        "requirement_value": 10,
        "reward_coins": 2000,
        "reward_stars": 50,
        "category": "social",
        "is_hidden": False
    },
    {
        "key": "shiny_hunter",
        "name": "✨ Shiny Hunter",
        "description": "Получите блестящего питомца",
        "icon": "✨",
        "requirement_type": "shiny_pet_owned",
        "requirement_value": 1,
        "reward_coins": 5000,
        "reward_stars": 150,
        "category": "special",
        "is_hidden": True
    },
]


async def init_achievements(session):
    """Initialize achievements in database"""
    try:
        # Check if achievements already exist
        result = await session.execute(select(Achievement).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info("Achievements already initialized, skipping...")
            return
        
        # Insert all achievements
        for ach_data in ACHIEVEMENTS:
            achievement = Achievement(**ach_data)
            session.add(achievement)
        
        await session.commit()
        logger.info(f"✅ Initialized {len(ACHIEVEMENTS)} achievements")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize achievements: {e}")
        await session.rollback()
        raise


async def init_database():
    """Initialize database with tables and data"""
    try:
        logger.info("Initializing database...")
        
        # Connect to database
        await db.connect()
        
        # Create tables
        await db.create_tables()
        
        # Initialize data
        async with db.get_session() as session:
            await init_achievements(session)
        
        logger.info("✅ Database initialized successfully!")
        
        # Close connection
        await db.disconnect()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    # Run initialization
    asyncio.run(init_database())
