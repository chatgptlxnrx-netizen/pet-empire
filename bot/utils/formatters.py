"""
Message formatters for beautiful output
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from bot.config import GameConstants


class Formatters:
    """Text formatting utilities"""
    
    @staticmethod
    def format_pet_card(pet: Dict, detailed: bool = False) -> str:
        """Format pet information card"""
        
        # Rarity with color
        rarity_colors = {
            "Common": "⚪️",
            "Uncommon": "🟢",
            "Rare": "🔵",
            "Epic": "🟣",
            "Legendary": "🟡",
            "Mythical": "🌈"
        }
        
        rarity_emoji = rarity_colors.get(pet.get("rarity", "Common"), "⚪️")
        
        # Status indicators
        status = []
        if pet.get("is_on_mission"):
            status.append("🚀 На миссии")
        if pet.get("is_defending"):
            status.append("🛡️ Защищает")
        if pet.get("fatigue_until") and pet["fatigue_until"] > datetime.now():
            status.append("😴 Устал")
        if pet.get("is_shiny"):
            status.append("✨ Блестящий")
        
        status_text = " | ".join(status) if status else "✅ Готов к действию"
        
        # Evolution stage
        evolution_emoji = "🌱" if pet.get("evolution_stage", 0) == 0 else "🌿" if pet.get("evolution_stage", 0) == 1 else "🌳"
        
        # Basic info
        text = f"""
{pet['emoji']} <b>{pet['name']}</b> {rarity_emoji}

<b>Тип:</b> {pet.get('pet_type', 'Unknown')}
<b>Редкость:</b> {pet.get('rarity', 'Common')}
<b>Статус:</b> {status_text}

{evolution_emoji} <b>Уровень:</b> {pet.get('level', 1)}/{GameConstants.MAX_PET_LEVEL}
📊 <b>Опыт:</b> {pet.get('exp', 0)}/{Formatters._calculate_exp_needed(pet.get('level', 1))}

⚡ <b>Сила:</b> {pet.get('power', 0)}
💰 <b>Доход:</b> {pet.get('income_per_hour', 0)}/час
❤️ <b>Верность:</b> {pet.get('loyalty', 50)}%
"""
        
        if detailed:
            text += f"""
🎯 <b>Выносливость:</b> {pet.get('stamina', 100)}%
💎 <b>Ценность:</b> {pet.get('total_value', 0):,} монет
📅 <b>Получен:</b> {pet.get('obtained_from', 'egg')}
"""
        
        return text.strip()
    
    @staticmethod
    def format_user_profile(user: Dict, pets_count: int = 0) -> str:
        """Format user profile"""
        
        # VIP badge
        vip_badge = "👑 VIP" if user.get("is_vip") else ""
        
        # Level progress
        exp_needed = Formatters._calculate_exp_needed(user.get("level", 1))
        exp_progress = (user.get("exp", 0) / exp_needed) * 100
        progress_bar = Formatters._create_progress_bar(exp_progress)
        
        text = f"""
👤 <b>{user.get('first_name', 'Игрок')}</b> {vip_badge}
@{user.get('username', 'unknown')}

📊 <b>Уровень:</b> {user.get('level', 1)}
{progress_bar} {user.get('exp', 0)}/{exp_needed} EXP

💰 <b>Монеты:</b> {user.get('coins', 0):,}
⭐ <b>Stars:</b> {user.get('stars', 0)}

🐾 <b>Питомцев:</b> {pets_count}/{user.get('pet_slots', 5)}

⚔️ <b>Рейды:</b> {user.get('raids_won', 0)} побед / {user.get('raids_lost', 0)} поражений
🛡️ <b>Защита:</b> {user.get('defenses_won', 0)} успешных / {user.get('defenses_lost', 0)} провалов

🎖️ <b>Battle Pass:</b> Уровень {user.get('battle_pass_level', 0)}/50
"""
        
        return text.strip()
    
    @staticmethod
    def format_mission_card(mission: Dict, pet_name: str = "") -> str:
        """Format mission information"""
        
        # Calculate time remaining
        now = datetime.now()
        complete_at = mission.get("complete_at", now)
        
        if isinstance(complete_at, str):
            complete_at = datetime.fromisoformat(complete_at.replace('Z', '+00:00'))
        
        if complete_at > now:
            time_left = complete_at - now
            time_str = Formatters.format_timedelta(time_left)
            status = f"⏱️ Осталось: {time_str}"
        else:
            status = "✅ Готово к сбору!"
        
        text = f"""
🚀 <b>{mission.get('mission_name', 'Миссия')}</b>

🐾 <b>Питомец:</b> {pet_name}
{status}

💰 <b>Награда:</b> {mission.get('reward_coins', 0)} монет
📊 <b>Опыт:</b> {mission.get('reward_exp', 0)} EXP
"""
        
        if mission.get("bonus_item"):
            text += f"🎁 <b>Бонус:</b> {mission['bonus_item']}\n"
        
        return text.strip()
    
    @staticmethod
    def format_raid_result(
        attacker_name: str,
        defender_name: str,
        result: str,
        attacker_power: int,
        defender_power: int,
        stolen_pet: Optional[str] = None
    ) -> str:
        """Format raid result"""
        
        if result == "win":
            text = f"""
🎉 <b>Победа в рейде!</b>

⚔️ <b>Атакующий:</b> {attacker_name} (Сила: {attacker_power})
🛡️ <b>Защищающийся:</b> {defender_name} (Сила: {defender_power})

✅ <b>Результат:</b> Успешная атака!
"""
            if stolen_pet:
                text += f"🎁 <b>Украден питомец:</b> {stolen_pet}\n"
            else:
                text += "⚠️ Питомец был слишком верен для кражи\n"
        else:
            text = f"""
😞 <b>Поражение в рейде</b>

⚔️ <b>Атакующий:</b> {attacker_name} (Сила: {attacker_power})
🛡️ <b>Защищающийся:</b> {defender_name} (Сила: {defender_power})

❌ <b>Результат:</b> Защита устояла!
😴 Ваши питомцы устали на 2 часа
"""
        
        return text.strip()
    
    @staticmethod
    def format_achievement(achievement: Dict, progress: Optional[Dict] = None) -> str:
        """Format achievement card"""
        
        completed = progress.get("completed", False) if progress else False
        current = progress.get("current_value", 0) if progress else 0
        required = achievement.get("requirement_value", 1)
        
        status = "✅ Выполнено" if completed else f"📊 {current}/{required}"
        
        progress_percent = (current / required * 100) if required > 0 else 0
        progress_bar = Formatters._create_progress_bar(progress_percent)
        
        text = f"""
{achievement.get('icon', '🏆')} <b>{achievement.get('name', 'Achievement')}</b>

{achievement.get('description', '')}

{status}
{progress_bar}

<b>Награда:</b>
"""
        
        if achievement.get("reward_coins", 0) > 0:
            text += f"💰 {achievement['reward_coins']} монет\n"
        if achievement.get("reward_stars", 0) > 0:
            text += f"⭐ {achievement['reward_stars']} Stars\n"
        if achievement.get("reward_item"):
            text += f"🎁 {achievement['reward_item']}\n"
        
        return text.strip()
    
    @staticmethod
    def format_leaderboard(
        entries: List[Dict],
        category: str,
        user_position: Optional[int] = None
    ) -> str:
        """Format leaderboard"""
        
        category_names = {
            "coins": "💰 Топ по монетам",
            "level": "📈 Топ по уровню",
            "raids": "⚔️ Топ по рейдам",
            "pets": "🐾 Топ по питомцам"
        }
        
        title = category_names.get(category, "👑 Лидерборд")
        
        text = f"<b>{title}</b>\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, entry in enumerate(entries[:10], 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            
            name = entry.get("first_name", "Unknown")
            username = entry.get("username", "")
            
            if category == "coins":
                value = f"{entry.get('coins', 0):,} 💰"
            elif category == "level":
                value = f"Уровень {entry.get('level', 1)}"
            elif category == "raids":
                value = f"{entry.get('raids_won', 0)} побед"
            else:  # pets
                value = f"{entry.get('pets_count', 0)} питомцев"
            
            highlight = " 👈" if user_position and i == user_position else ""
            
            text += f"{medal} <b>{name}</b> (@{username}) - {value}{highlight}\n"
        
        if user_position and user_position > 10:
            text += f"\n...\n\n📍 Ваша позиция: #{user_position}"
        
        return text.strip()
    
    @staticmethod
    def format_timedelta(td: timedelta) -> str:
        """Format timedelta to human readable string"""
        total_seconds = int(td.total_seconds())
        
        if total_seconds <= 0:
            return "0 секунд"
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}ч")
        if minutes > 0:
            parts.append(f"{minutes}м")
        if seconds > 0 and hours == 0:
            parts.append(f"{seconds}с")
        
        return " ".join(parts)
    
    @staticmethod
    def _create_progress_bar(percent: float, length: int = 10) -> str:
        """Create a text progress bar"""
        filled = int(percent / 100 * length)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}] {percent:.1f}%"
    
    @staticmethod
    def _calculate_exp_needed(level: int) -> int:
        """Calculate EXP needed for level up"""
        return int(GameConstants.EXP_PER_LEVEL * (1.1 ** level))
    
    @staticmethod
    def format_coins(amount: int) -> str:
        """Format coin amount with thousands separator"""
        return f"{amount:,}"
    
    @staticmethod
    def format_notification(title: str, message: str, icon: str = "ℹ️") -> str:
        """Format notification message"""
        return f"{icon} <b>{title}</b>\n\n{message}"
    
    @staticmethod
    def format_error(message: str) -> str:
        """Format error message"""
        return f"❌ <b>Ошибка</b>\n\n{message}"
    
    @staticmethod
    def format_success(message: str) -> str:
        """Format success message"""
        return f"✅ <b>Успешно!</b>\n\n{message}"
    
    @staticmethod
    def format_welcome() -> str:
        """Format welcome message"""
        return """
🎉 <b>Добро пожаловать в Pet Empire!</b>

🐾 Собирай уникальных питомцев
🚀 Отправляй их на миссии
⚔️ Сражайся с другими игроками
💰 Зарабатывай монеты и Stars
🏆 Достигай вершин лидерборда!

Получи своё первое бесплатное яйцо! 🥚
"""
