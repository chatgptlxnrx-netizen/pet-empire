"""
Main bot file - entry point
"""
import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import settings
from bot.database.db import db
from bot.middlewares.database import DatabaseMiddleware

# Import handlers
from bot.handlers import start, pets, missions, raids, shop, leaderboard


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)


async def on_startup(bot: Bot):
    """Actions on startup"""
    logger.info("🚀 Starting Pet Empire Bot...")
    
    # Connect to database
    await db.connect()
    
    # Create tables if not exist
    await db.create_tables()
    
    # Start scheduler for background tasks
    scheduler = AsyncIOScheduler()
    
    # Check for completed missions every minute
    async def check_missions():
        from bot.services.mission_service import MissionService
        async with db.get_session() as session:
            try:
                await MissionService.check_and_autocomplete_missions(session)
            except Exception as e:
                logger.error(f"Error in mission check: {e}")
    
    scheduler.add_job(check_missions, 'interval', minutes=1)
    scheduler.start()
    
    # Set bot commands
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="pets", description="🐾 Мои питомцы"),
        BotCommand(command="missions", description="🚀 Миссии"),
        BotCommand(command="raids", description="⚔️ Рейды"),
        BotCommand(command="shop", description="🛒 Магазин"),
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="help", description="❓ Помощь"),
    ]
    await bot.set_my_commands(commands)
    
    logger.info("✅ Bot started successfully!")


async def on_shutdown(bot: Bot):
    """Actions on shutdown"""
    logger.info("Shutting down bot...")
    
    # Close database
    await db.disconnect()
    
    logger.info("Bot stopped")


async def main():
    """Main function"""
    
    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )
    
    # Initialize dispatcher
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Add middleware
    dp.update.middleware(DatabaseMiddleware())
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(pets.router)
    dp.include_router(missions.router)
    dp.include_router(raids.router)
    dp.include_router(shop.router)
    dp.include_router(leaderboard.router)
    
    # Register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
