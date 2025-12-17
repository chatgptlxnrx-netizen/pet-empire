"""Raids handler"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services import RaidService, PetService
from bot.utils import Keyboards, Formatters

router = Router()

@router.message(Command("raids"))
@router.callback_query(F.data == "raids_menu")
async def raids_menu(event: Message | CallbackQuery, session: AsyncSession):
    """Show raids menu"""
    if isinstance(event, Message):
        user_id, send_func = event.from_user.id, event.answer
    else:
        user_id, send_func = event.from_user.id, event.message.edit_text
        await event.answer()
    
    stats = await RaidService.get_raid_stats(session, user_id)
    text = f"""⚔️ <b>Рейды</b>

📊 Статистика:
Побед: {stats['raids_won']} | Поражений: {stats['raids_lost']}
Winrate: {stats['win_rate']}%

🎯 Бесплатных атак сегодня: {stats['free_raids_today']}/5"""
    
    await send_func(text, reply_markup=Keyboards.raid_menu())

@router.callback_query(F.data == "start_raid")
async def start_raid(callback: CallbackQuery, session: AsyncSession):
    """Start raid - select target"""
    pets = await PetService.get_available_pets_for_raid(session, callback.from_user.id)
    if not pets:
        await callback.answer("Нет доступных питомцев для атаки!", show_alert=True)
        return
    
    targets = await RaidService.get_raid_targets(session, callback.from_user.id)
    if not targets:
        await callback.answer("Нет доступных целей!", show_alert=True)
        return
    
    text = "🎯 <b>Выберите цель</b>\n\n"
    for t in targets[:5]:
        text += f"• {t.first_name} (Lv.{t.level}) - {len(await PetService.get_user_pets(session, t.user_id))} питомцев\n"
    
    # For demo, attack first target
    target = targets[0]
    pets_data = [{"id": p.id, "name": p.name, "emoji": p.emoji, "power": p.power} for p in pets]
    await callback.message.edit_text(f"⚔️ Выберите питомцев для атаки\nЦель: {target.first_name}",
                                    reply_markup=Keyboards.raid_pet_selection(pets_data))
    await callback.answer()
