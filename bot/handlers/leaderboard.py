"""Leaderboard handler"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from bot.database.models import User, Pet
from bot.utils import Keyboards, Formatters

router = Router()

@router.callback_query(F.data == "leaderboard")
async def leaderboard_menu(callback: CallbackQuery):
    """Show leaderboard menu"""
    text = "👑 <b>Лидерборд</b>\n\nВыберите категорию:"
    await callback.message.edit_text(text, reply_markup=Keyboards.leaderboard_categories())
    await callback.answer()

@router.callback_query(F.data.startswith("lb:"))
async def show_leaderboard(callback: CallbackQuery, session: AsyncSession):
    """Show specific leaderboard"""
    category = callback.data.split(":")[1]
    
    if category == "coins":
        result = await session.execute(select(User).order_by(User.coins.desc()).limit(10))
    elif category == "level":
        result = await session.execute(select(User).order_by(User.level.desc(), User.exp.desc()).limit(10))
    elif category == "raids":
        result = await session.execute(select(User).order_by(User.raids_won.desc()).limit(10))
    else:  # pets
        result = await session.execute(
            select(User, func.count(Pet.id).label('pets_count'))
            .join(Pet, Pet.owner_id == User.user_id)
            .group_by(User.user_id)
            .order_by(func.count(Pet.id).desc())
            .limit(10)
        )
    
    entries = [{"first_name": u.first_name, "username": u.username or "unknown",
                "coins": u.coins, "level": u.level, "raids_won": u.raids_won} for u in result.scalars()]
    
    text = Formatters.format_leaderboard(entries, category)
    await callback.message.edit_text(text, reply_markup=Keyboards.back_to_menu())
    await callback.answer()
