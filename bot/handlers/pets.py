"""Pet management handler"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import User
from bot.services import PetService, AchievementService
from bot.utils import Keyboards, Formatters, ImageGenerator

router = Router()

@router.message(Command("pets"))
@router.callback_query(F.data == "my_pets")
async def show_pets(event: Message | CallbackQuery, session: AsyncSession):
    """Show user's pets"""
    if isinstance(event, Message):
        user_id, send_func = event.from_user.id, event.answer
    else:
        user_id, send_func = event.from_user.id, event.message.edit_text
        await event.answer()
    
    pets = await PetService.get_user_pets(session, user_id)
    if not pets:
        await send_func("У вас пока нет питомцев! 🥚\nОткройте яйцо из магазина.", reply_markup=Keyboards.main_menu())
        return
    
    pets_data = [{"id": p.id, "name": p.name, "emoji": p.emoji, "level": p.level, "rarity": p.rarity,
                  "is_on_mission": p.is_on_mission, "is_defending": p.is_defending, "fatigue_until": p.fatigue_until}
                 for p in pets]
    text = f"🐾 <b>Ваши питомцы</b> ({len(pets)})\n\nВыберите питомца:"
    await send_func(text, reply_markup=Keyboards.pet_list(pets_data))

@router.callback_query(F.data.startswith("view_pet:"))
async def view_pet(callback: CallbackQuery, session: AsyncSession):
    """View pet details"""
    pet_id = int(callback.data.split(":")[1])
    pet = await PetService.get_pet_by_id(session, pet_id, callback.from_user.id)
    if not pet:
        await callback.answer("Питомец не найден!", show_alert=True)
        return
    
    pet_dict = {"id": pet.id, "name": pet.name, "emoji": pet.emoji, "pet_type": pet.pet_type,
                "rarity": pet.rarity, "level": pet.level, "exp": pet.exp, "power": pet.power,
                "income_per_hour": pet.income_per_hour, "loyalty": pet.loyalty, "stamina": pet.stamina,
                "is_on_mission": pet.is_on_mission, "is_defending": pet.is_defending, "is_shiny": pet.is_shiny,
                "evolution_stage": pet.evolution_stage, "obtained_from": pet.obtained_from}
    
    text = Formatters.format_pet_card(pet_dict, detailed=True)
    await callback.message.edit_text(text, reply_markup=Keyboards.pet_actions(pet.id, pet.is_on_mission, pet.is_defending))
    await callback.answer()

@router.callback_query(F.data == "open_egg")
async def open_egg_menu(callback: CallbackQuery, session: AsyncSession):
    """Open egg menu"""
    result = await session.execute(select(User).where(User.user_id == callback.from_user.id))
    user = result.scalar_one_or_none()
    if not user:
        await callback.answer("Используйте /start", show_alert=True)
        return
    
    pets_count = len(await PetService.get_user_pets(session, user.user_id))
    if pets_count >= user.pet_slots:
        await callback.answer(f"Нет места! ({pets_count}/{user.pet_slots})\nКупите слоты в магазине.", show_alert=True)
        return
    
    text = f"🥚 <b>Открыть яйцо</b>\n\nСлотов: {pets_count}/{user.pet_slots}\nМонеты: {user.coins:,} 💰\nStars: {user.stars} ⭐"
    await callback.message.edit_text(text, reply_markup=Keyboards.egg_shop())
    await callback.answer()

@router.callback_query(F.data.startswith("buy_egg:"))
async def buy_egg(callback: CallbackQuery, session: AsyncSession):
    """Buy and open egg"""
    egg_type = callback.data.split(":")[1]
    result = await session.execute(select(User).where(User.user_id == callback.from_user.id))
    user = result.scalar_one_or_none()
    
    from bot.config import GameConstants
    cost = GameConstants.EGG_COSTS.get(egg_type, {"coins": 0, "stars": 0})
    
    if cost["coins"] > 0 and user.coins < cost["coins"]:
        await callback.answer("Недостаточно монет!", show_alert=True)
        return
    if cost["stars"] > 0 and user.stars < cost["stars"]:
        await callback.answer("Недостаточно Stars!", show_alert=True)
        return
    
    user.coins -= cost["coins"]
    user.stars -= cost["stars"]
    pet = await PetService.create_pet(session, user.user_id, egg_type)
    await AchievementService.check_and_update_achievements(session, user.user_id, "pets_owned", 1)
    
    pet_dict = {"id": pet.id, "name": pet.name, "emoji": pet.emoji, "pet_type": pet.pet_type,
                "rarity": pet.rarity, "level": pet.level, "power": pet.power, "income_per_hour": pet.income_per_hour}
    
    text = f"🎉 <b>Поздравляем!</b>\n\n{Formatters.format_pet_card(pet_dict)}"
    await callback.message.edit_text(text, reply_markup=Keyboards.back_to_menu())
    await callback.answer("🎉 Новый питомец!")
