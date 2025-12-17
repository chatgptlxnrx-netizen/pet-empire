"""
Start handler - registration and main menu
"""
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.database.models import User
from bot.services import PetService, AchievementService
from bot.utils import Keyboards, Formatters
from bot.config import settings

router = Router()


async def get_or_create_user(session: AsyncSession, message: Message) -> User:
    """Get existing user or create new one"""
    
    user_id = message.from_user.id
    
    # Try to get existing user
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Update last active
        from datetime import datetime
        user.last_active = datetime.now()
        await session.commit()
        return user
    
    # Create new user
    user = User(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        coins=settings.starting_coins,
        pet_slots=settings.starting_slots
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Give starter pet
    await PetService.create_pet(session, user_id, "common")
    
    # Track achievement
    await AchievementService.check_and_update_achievements(
        session,
        user_id,
        "pets_owned",
        1
    )
    
    return user


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Start command - welcome new users"""
    
    user = await get_or_create_user(session, message)
    
    if not user.tutorial_completed:
        # Show tutorial
        text = Formatters.format_welcome()
        user.tutorial_completed = True
        await session.commit()
    else:
        # Returning user
        pets_count = len(await PetService.get_user_pets(session, user.user_id))
        text = Formatters.format_user_profile(
            {
                "first_name": user.first_name,
                "username": user.username or "unknown",
                "level": user.level,
                "exp": user.exp,
                "coins": user.coins,
                "stars": user.stars,
                "pet_slots": user.pet_slots,
                "raids_won": user.raids_won,
                "raids_lost": user.raids_lost,
                "defenses_won": user.defenses_won,
                "defenses_lost": user.defenses_lost,
                "battle_pass_level": user.battle_pass_level,
                "is_vip": user.is_vip
            },
            pets_count
        )
    
    await message.answer(
        text,
        reply_markup=Keyboards.main_menu(user.level)
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    
    text = """
<b>🎮 Pet Empire - Помощь</b>

<b>Основные команды:</b>
/start - Главное меню
/pets - Мои питомцы
/missions - Активные миссии
/raids - Рейды
/shop - Магазин
/stats - Статистика

<b>Как играть:</b>
🥚 Открывай яйца и получай питомцев
🚀 Отправляй их на миссии за награды
⚔️ Атакуй других игроков в рейдах
🛡️ Защищай свою коллекцию
💰 Зарабатывай монеты и Stars
🏆 Выполняй достижения

<b>Редкость питомцев:</b>
⚪️ Common (50%)
🟢 Uncommon (30%)
🔵 Rare (15%)
🟣 Epic (4%)
🟡 Legendary (0.9%)
🌈 Mythical (0.1%)

<b>Монетизация:</b>
💰 Монеты - внутриигровая валюта
⭐ Stars - премиум валюта (Telegram Stars)

Удачи! 🎉
"""
    
    await message.answer(text, reply_markup=Keyboards.back_to_menu())


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, session: AsyncSession):
    """Show main menu"""
    
    user_id = callback.from_user.id
    
    # Get user
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await callback.answer("Пожалуйста, используйте /start", show_alert=True)
        return
    
    pets_count = len(await PetService.get_user_pets(session, user.user_id))
    
    text = Formatters.format_user_profile(
        {
            "first_name": user.first_name,
            "username": user.username or "unknown",
            "level": user.level,
            "exp": user.exp,
            "coins": user.coins,
            "stars": user.stars,
            "pet_slots": user.pet_slots,
            "raids_won": user.raids_won,
            "raids_lost": user.raids_lost,
            "defenses_won": user.defenses_won,
            "defenses_lost": user.defenses_lost,
            "battle_pass_level": user.battle_pass_level,
            "is_vip": user.is_vip
        },
        pets_count
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=Keyboards.main_menu(user.level)
    )
    await callback.answer()


@router.message(Command("stats"))
@router.callback_query(F.data == "stats")
async def show_stats(event: Message | CallbackQuery, session: AsyncSession):
    """Show user statistics"""
    
    if isinstance(event, Message):
        user_id = event.from_user.id
        send_func = event.answer
    else:
        user_id = event.from_user.id
        send_func = event.message.edit_text
        await event.answer()
    
    # Get user
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await send_func("Используйте /start для начала")
        return
    
    # Get pets info
    pets = await PetService.get_user_pets(session, user_id)
    rarity_counts = await PetService.count_pets_by_rarity(session, user_id)
    collection_value = await PetService.get_total_collection_value(session, user_id)
    
    # Get achievement stats
    achievement_stats = await AchievementService.get_achievement_stats(session, user_id)
    
    # Get raid stats
    from bot.services import RaidService
    raid_stats = await RaidService.get_raid_stats(session, user_id)
    
    text = f"""
📊 <b>Статистика</b>

👤 <b>Профиль:</b>
Уровень: {user.level}
Монеты: {user.coins:,} 💰
Stars: {user.stars} ⭐

🐾 <b>Коллекция:</b>
Всего питомцев: {len(pets)}/{user.pet_slots}
Ценность: {collection_value:,} 💰

<b>По редкости:</b>
⚪️ Common: {rarity_counts.get('Common', 0)}
🟢 Uncommon: {rarity_counts.get('Uncommon', 0)}
🔵 Rare: {rarity_counts.get('Rare', 0)}
🟣 Epic: {rarity_counts.get('Epic', 0)}
🟡 Legendary: {rarity_counts.get('Legendary', 0)}
🌈 Mythical: {rarity_counts.get('Mythical', 0)}

⚔️ <b>Рейды:</b>
Побед: {raid_stats.get('raids_won', 0)}
Поражений: {raid_stats.get('raids_lost', 0)}
Winrate: {raid_stats.get('win_rate', 0)}%

🛡️ <b>Защита:</b>
Успешных: {raid_stats.get('defenses_won', 0)}
Провалов: {raid_stats.get('defenses_lost', 0)}
Success rate: {raid_stats.get('defense_rate', 0)}%

🏆 <b>Достижения:</b>
Выполнено: {achievement_stats.get('completed', 0)}/{achievement_stats.get('total', 0)}
Прогресс: {achievement_stats.get('completion_rate', 0)}%
"""
    
    await send_func(text, reply_markup=Keyboards.back_to_menu())
