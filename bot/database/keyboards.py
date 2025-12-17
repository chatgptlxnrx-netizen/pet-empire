"""
Inline keyboards for beautiful UI
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Keyboards:
    """Keyboard factory"""
    
    @staticmethod
    def main_menu(user_level: int = 1) -> InlineKeyboardMarkup:
        """Main menu keyboard"""
        builder = InlineKeyboardBuilder()
        
        # Row 1: Main actions
        builder.row(
            InlineKeyboardButton(text="🐾 Мои Питомцы", callback_data="my_pets"),
            InlineKeyboardButton(text="🥚 Открыть Яйцо", callback_data="open_egg")
        )
        
        # Row 2: Missions and Raids
        builder.row(
            InlineKeyboardButton(text="🚀 Миссии", callback_data="missions"),
            InlineKeyboardButton(text="⚔️ Рейды", callback_data="raids_menu")
        )
        
        # Row 3: Trading and Defense
        builder.row(
            InlineKeyboardButton(text="🤝 Обмен", callback_data="trade_menu"),
            InlineKeyboardButton(text="🛡️ Защита", callback_data="defense_menu")
        )
        
        # Row 4: Progression
        builder.row(
            InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
        )
        
        # Row 5: Shop and Leaderboard
        builder.row(
            InlineKeyboardButton(text="🛒 Магазин", callback_data="shop"),
            InlineKeyboardButton(text="👑 Топ Игроков", callback_data="leaderboard")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def pet_list(
        pets: List[dict],
        page: int = 0,
        per_page: int = 5,
        action: str = "view"
    ) -> InlineKeyboardMarkup:
        """Pet list with pagination"""
        builder = InlineKeyboardBuilder()
        
        start = page * per_page
        end = start + per_page
        page_pets = pets[start:end]
        
        # Pet buttons
        for pet in page_pets:
            status = ""
            if pet.get("is_on_mission"):
                status = " 🚀"
            elif pet.get("is_defending"):
                status = " 🛡️"
            elif pet.get("fatigue_until"):
                status = " 😴"
            
            rarity_color = {
                "Common": "⚪️",
                "Uncommon": "🟢",
                "Rare": "🔵",
                "Epic": "🟣",
                "Legendary": "🟡",
                "Mythical": "🌈"
            }.get(pet["rarity"], "⚪️")
            
            text = f"{pet['emoji']} {pet['name']} Lv.{pet['level']} {rarity_color}{status}"
            builder.row(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"{action}_pet:{pet['id']}"
                )
            )
        
        # Pagination
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"pets_page:{page-1}")
            )
        if end < len(pets):
            nav_buttons.append(
                InlineKeyboardButton(text="Вперед ➡️", callback_data=f"pets_page:{page+1}")
            )
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        # Back button
        builder.row(
            InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def pet_actions(pet_id: int, is_on_mission: bool = False, is_defending: bool = False) -> InlineKeyboardMarkup:
        """Actions for a specific pet"""
        builder = InlineKeyboardBuilder()
        
        if not is_on_mission and not is_defending:
            builder.row(
                InlineKeyboardButton(text="🚀 Отправить на миссию", callback_data=f"send_mission:{pet_id}")
            )
            builder.row(
                InlineKeyboardButton(text="🛡️ Назначить защитником", callback_data=f"set_defender:{pet_id}"),
                InlineKeyboardButton(text="📈 Улучшить", callback_data=f"upgrade_pet:{pet_id}")
            )
        
        if is_on_mission:
            builder.row(
                InlineKeyboardButton(text="⏱️ Статус миссии", callback_data=f"mission_status:{pet_id}")
            )
        
        if is_defending:
            builder.row(
                InlineKeyboardButton(text="🏠 Убрать с защиты", callback_data=f"remove_defender:{pet_id}")
            )
        
        # Bottom row
        builder.row(
            InlineKeyboardButton(text="⬅️ К списку", callback_data="my_pets"),
            InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def mission_selection(pet_id: int) -> InlineKeyboardMarkup:
        """Mission type selection"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="⚡ Быстрая (30 мин) - 50 💰",
                callback_data=f"start_mission:{pet_id}:quick"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🎯 Средняя (3 часа) - 200 💰",
                callback_data=f"start_mission:{pet_id}:medium"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🌟 Длинная (8 часов) - 800 💰",
                callback_data=f"start_mission:{pet_id}:long"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="💎 Эпическая (12 часов) - 2000 💰",
                callback_data=f"start_mission:{pet_id}:epic"
            )
        )
        
        builder.row(
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_pet:{pet_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def raid_menu() -> InlineKeyboardMarkup:
        """Raid menu"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="⚔️ Атаковать игрока", callback_data="start_raid")
        )
        builder.row(
            InlineKeyboardButton(text="📜 История рейдов", callback_data="raid_history")
        )
        builder.row(
            InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def raid_pet_selection(pets: List[dict], selected: List[int] = None) -> InlineKeyboardMarkup:
        """Select pets for raid"""
        builder = InlineKeyboardBuilder()
        selected = selected or []
        
        for pet in pets[:5]:  # Max 5 pets for selection
            status = "✅ " if pet["id"] in selected else ""
            text = f"{status}{pet['emoji']} {pet['name']} (⚡{pet['power']})"
            builder.row(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"toggle_raid_pet:{pet['id']}"
                )
            )
        
        if selected:
            total_power = sum(p["power"] for p in pets if p["id"] in selected)
            builder.row(
                InlineKeyboardButton(
                    text=f"🎯 Начать атаку (Сила: {total_power})",
                    callback_data=f"confirm_raid:{','.join(map(str, selected))}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="❌ Отмена", callback_data="raids_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def defense_menu() -> InlineKeyboardMarkup:
        """Defense management"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🛡️ Мои защитники", callback_data="view_defenders")
        )
        builder.row(
            InlineKeyboardButton(text="🔧 Купить ловушки", callback_data="buy_traps")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Статистика защиты", callback_data="defense_stats")
        )
        builder.row(
            InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def shop_menu() -> InlineKeyboardMarkup:
        """Shop menu"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🥚 Купить яйца", callback_data="shop_eggs")
        )
        builder.row(
            InlineKeyboardButton(text="⚡ Ускорители", callback_data="shop_boosters")
        )
        builder.row(
            InlineKeyboardButton(text="🛡️ Защита", callback_data="shop_defense")
        )
        builder.row(
            InlineKeyboardButton(text="💎 VIP статус", callback_data="shop_vip")
        )
        builder.row(
            InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def egg_shop() -> InlineKeyboardMarkup:
        """Egg shop"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="⚪️ Обычное яйцо - 50 💰", callback_data="buy_egg:common")
        )
        builder.row(
            InlineKeyboardButton(text="🔵 Редкое яйцо - 100 ⭐", callback_data="buy_egg:rare")
        )
        builder.row(
            InlineKeyboardButton(text="🟣 Эпическое яйцо - 250 ⭐", callback_data="buy_egg:epic")
        )
        builder.row(
            InlineKeyboardButton(text="🟡 Легендарное яйцо - 500 ⭐", callback_data="buy_egg:legendary")
        )
        builder.row(
            InlineKeyboardButton(text="🌈 Мифическое яйцо - 1000 ⭐", callback_data="buy_egg:mythical")
        )
        
        builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="shop")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def confirm_purchase(item: str, cost: int, currency: str = "coins") -> InlineKeyboardMarkup:
        """Confirm purchase"""
        builder = InlineKeyboardBuilder()
        
        currency_emoji = "💰" if currency == "coins" else "⭐"
        
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Купить за {cost} {currency_emoji}",
                callback_data=f"confirm_buy:{item}:{currency}"
            )
        )
        builder.row(
            InlineKeyboardButton(text="❌ Отмена", callback_data="shop")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        """Simple back button"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")
        )
        return builder.as_markup()
    
    @staticmethod
    def achievement_categories() -> InlineKeyboardMarkup:
        """Achievement categories"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="📦 Коллекция", callback_data="ach_cat:collection"),
            InlineKeyboardButton(text="🚀 Миссии", callback_data="ach_cat:missions")
        )
        builder.row(
            InlineKeyboardButton(text="⚔️ Рейды", callback_data="ach_cat:raids"),
            InlineKeyboardButton(text="💰 Богатство", callback_data="ach_cat:wealth")
        )
        builder.row(
            InlineKeyboardButton(text="📈 Прогресс", callback_data="ach_cat:progression"),
            InlineKeyboardButton(text="✨ Особые", callback_data="ach_cat:special")
        )
        
        builder.row(
            InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def leaderboard_categories() -> InlineKeyboardMarkup:
        """Leaderboard categories"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="💰 По монетам", callback_data="lb:coins")
        )
        builder.row(
            InlineKeyboardButton(text="📈 По уровню", callback_data="lb:level")
        )
        builder.row(
            InlineKeyboardButton(text="⚔️ По рейдам", callback_data="lb:raids")
        )
        builder.row(
            InlineKeyboardButton(text="🐾 По питомцам", callback_data="lb:pets")
        )
        
        builder.row(
            InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")
        )
        
        return builder.as_markup()
