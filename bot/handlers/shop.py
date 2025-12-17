"""Shop handler"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import User
from bot.utils import Keyboards

router = Router()

@router.callback_query(F.data == "shop")
async def shop_menu(callback: CallbackQuery, session: AsyncSession):
    """Show shop menu"""
    result = await session.execute(select(User).where(User.user_id == callback.from_user.id))
    user = result.scalar_one_or_none()
    text = f"🛒 <b>Магазин</b>\n\nМонеты: {user.coins:,} 💰\nStars: {user.stars} ⭐"
    await callback.message.edit_text(text, reply_markup=Keyboards.shop_menu())
    await callback.answer()

@router.callback_query(F.data == "shop_eggs")
async def shop_eggs(callback: CallbackQuery):
    """Show egg shop"""
    text = "🥚 <b>Магазин яиц</b>\n\nВыберите яйцо:"
    await callback.message.edit_text(text, reply_markup=Keyboards.egg_shop())
    await callback.answer()

@router.callback_query(F.data.startswith("shop_"))
async def shop_category(callback: CallbackQuery):
    """Other shop categories"""
    await callback.answer("В разработке! 🚧", show_alert=True)
