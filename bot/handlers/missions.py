"""Missions handler"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from bot.services import PetService, MissionService, AchievementService
from bot.utils import Keyboards, Formatters

router = Router()

@router.message(Command("missions"))
@router.callback_query(F.data == "missions")
async def show_missions(event: Message | CallbackQuery, session: AsyncSession):
    """Show active missions"""
    if isinstance(event, Message):
        user_id, send_func = event.from_user.id, event.answer
    else:
        user_id, send_func = event.from_user.id, event.message.edit_text
        await event.answer()
    
    missions = await MissionService.get_active_missions(session, user_id)
    if not missions:
        await send_func("У вас нет активных миссий.\nОтправьте питомца на миссию!", reply_markup=Keyboards.back_to_menu())
        return
    
    text = "🚀 <b>Активные миссии</b>\n\n"
    for m in missions:
        pet = await PetService.get_pet_by_id(session, m.pet_id)
        time_left = m.complete_at - datetime.now()
        status = "✅ Готово!" if time_left.total_seconds() <= 0 else f"⏱️ {Formatters.format_timedelta(time_left)}"
        text += f"• {pet.emoji} {pet.name}\n  {m.mission_name}\n  {status}\n\n"
    
    await send_func(text, reply_markup=Keyboards.back_to_menu())

@router.callback_query(F.data.startswith("send_mission:"))
async def send_on_mission(callback: CallbackQuery, session: AsyncSession):
    """Send pet on mission"""
    pet_id = int(callback.data.split(":")[1])
    pet = await PetService.get_pet_by_id(session, pet_id, callback.from_user.id)
    if not pet:
        await callback.answer("Питомец не найден!", show_alert=True)
        return
    
    text = f"🚀 <b>Выберите миссию для {pet.name}</b>\n\nСила: {pet.power} | Уровень: {pet.level}"
    await callback.message.edit_text(text, reply_markup=Keyboards.mission_selection(pet_id))
    await callback.answer()

@router.callback_query(F.data.startswith("start_mission:"))
async def start_mission(callback: CallbackQuery, session: AsyncSession):
    """Start mission"""
    parts = callback.data.split(":")
    pet_id, mission_type = int(parts[1]), parts[2]
    pet = await PetService.get_pet_by_id(session, pet_id, callback.from_user.id)
    
    try:
        mission = await MissionService.start_mission(session, pet, mission_type)
        await AchievementService.check_and_update_achievements(session, callback.from_user.id, "missions_completed", 0)
        
        mission_dict = {"mission_name": mission.mission_name, "complete_at": mission.complete_at,
                       "reward_coins": mission.reward_coins, "reward_exp": mission.reward_exp}
        text = f"✅ <b>Миссия начата!</b>\n\n{Formatters.format_mission_card(mission_dict, pet.name)}"
        await callback.message.edit_text(text, reply_markup=Keyboards.back_to_menu())
        await callback.answer("🚀 Питомец отправлен!")
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
