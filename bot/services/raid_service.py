"""
Raid service - PvP raid mechanics
"""
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.database.models import Raid, Pet, User
from bot.services.pet_service import PetService
from bot.config import GameConstants


class RaidService:
    """Raid/PvP management service"""
    
    @staticmethod
    async def can_raid_target(
        session: AsyncSession,
        attacker_id: int,
        defender_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if attacker can raid defender"""
        
        # Can't raid yourself
        if attacker_id == defender_id:
            return False, "Нельзя атаковать самого себя"
        
        # Check attacker's free raids
        attacker = await session.get(User, attacker_id)
        if not attacker:
            return False, "User not found"
        
        # Reset daily raids if needed
        if attacker.last_raid_reset:
            if attacker.last_raid_reset.date() < datetime.now().date():
                attacker.free_raids_today = GameConstants.DAILY_FREE_RAIDS
                attacker.last_raid_reset = datetime.now()
                await session.commit()
        else:
            attacker.last_raid_reset = datetime.now()
            await session.commit()
        
        if attacker.free_raids_today <= 0:
            return False, f"Нет бесплатных атак. Осталось: {attacker.free_raids_today}"
        
        # Check cooldown on this specific target
        result = await session.execute(
            select(Raid).where(
                and_(
                    Raid.attacker_id == attacker_id,
                    Raid.defender_id == defender_id,
                    Raid.timestamp > datetime.now() - timedelta(seconds=GameConstants.RAID_COOLDOWN)
                )
            ).order_by(Raid.timestamp.desc()).limit(1)
        )
        
        last_raid = result.scalar_one_or_none()
        if last_raid:
            time_left = (last_raid.timestamp + timedelta(seconds=GameConstants.RAID_COOLDOWN)) - datetime.now()
            hours = int(time_left.total_seconds() / 3600)
            minutes = int((time_left.total_seconds() % 3600) / 60)
            return False, f"Можно атаковать снова через {hours}ч {minutes}м"
        
        # Check defender's shield
        defender = await session.get(User, defender_id)
        if defender and defender.raid_shield_until:
            if defender.raid_shield_until > datetime.now():
                time_left = defender.raid_shield_until - datetime.now()
                minutes = int(time_left.total_seconds() / 60)
                return False, f"Игрок под защитой еще {minutes} минут"
        
        return True, None
    
    @staticmethod
    async def execute_raid(
        session: AsyncSession,
        attacker_id: int,
        defender_id: int,
        attacker_pet_ids: List[int]
    ) -> Dict[str, any]:
        """Execute a raid"""
        
        # Verify can raid
        can_raid, error = await RaidService.can_raid_target(session, attacker_id, defender_id)
        if not can_raid:
            raise ValueError(error)
        
        # Get attacker pets
        attacker_pets = []
        for pet_id in attacker_pet_ids:
            pet = await session.get(Pet, pet_id)
            if pet and pet.owner_id == attacker_id:
                attacker_pets.append(pet)
        
        if not attacker_pets:
            raise ValueError("No valid pets for attack")
        
        # Calculate attack power
        attack_power = sum(pet.power * pet.level for pet in attacker_pets)
        
        # Calculate defense power
        defense_power = await PetService.calculate_total_defense_power(session, defender_id)
        
        # Calculate win chance
        total_power = attack_power + defense_power
        if total_power == 0:
            win_chance = 0.5
        else:
            win_chance = attack_power / total_power
        
        # Add randomness ±15%
        win_chance += random.uniform(-0.15, 0.15)
        win_chance = max(0.1, min(0.9, win_chance))  # Clamp between 10% and 90%
        
        # Determine result
        success = random.random() < win_chance
        
        stolen_pet = None
        
        if success:
            # Victory - try to steal a pet
            stealable_pets = await PetService.get_stealable_pets(session, defender_id)
            
            if stealable_pets:
                # Select random pet
                target_pet = random.choice(stealable_pets)
                
                # Check loyalty
                if await PetService.can_steal_pet(target_pet):
                    # Transfer pet
                    transfer_success = await PetService.transfer_pet(
                        session,
                        target_pet,
                        attacker_id,
                        "raid"
                    )
                    
                    if transfer_success:
                        stolen_pet = target_pet
            
            # Give shield to attacker
            attacker = await session.get(User, attacker_id)
            attacker.raid_shield_until = datetime.now() + timedelta(seconds=GameConstants.RAID_SHIELD_DURATION)
            attacker.raids_won += 1
            attacker.free_raids_today -= 1
            
            # Update defender stats
            defender = await session.get(User, defender_id)
            defender.defenses_lost += 1
            
            result_data = {
                "success": True,
                "attack_power": attack_power,
                "defense_power": defense_power,
                "stolen_pet": stolen_pet.id if stolen_pet else None,
                "stolen_pet_name": stolen_pet.name if stolen_pet else None,
                "win_chance": round(win_chance * 100, 1)
            }
            
            logger.info(f"Raid success: {attacker_id} -> {defender_id}, stole: {stolen_pet.id if stolen_pet else 'none'}")
            
        else:
            # Defeat - fatigue attacker's pets
            for pet in attacker_pets:
                await PetService.set_pet_fatigue(session, pet, hours=2)
            
            # Update stats
            attacker = await session.get(User, attacker_id)
            attacker.raids_lost += 1
            attacker.free_raids_today -= 1
            
            defender = await session.get(User, defender_id)
            defender.defenses_won += 1
            
            result_data = {
                "success": False,
                "attack_power": attack_power,
                "defense_power": defense_power,
                "stolen_pet": None,
                "stolen_pet_name": None,
                "win_chance": round(win_chance * 100, 1)
            }
            
            logger.info(f"Raid failed: {attacker_id} -> {defender_id}")
        
        # Log raid
        raid = Raid(
            attacker_id=attacker_id,
            defender_id=defender_id,
            attacker_power=attack_power,
            defender_power=defense_power,
            result="win" if success else "lose",
            stolen_pet_id=stolen_pet.id if stolen_pet else None
        )
        
        session.add(raid)
        await session.commit()
        
        return result_data
    
    @staticmethod
    async def get_raid_targets(
        session: AsyncSession,
        attacker_id: int,
        limit: int = 10
    ) -> List[User]:
        """Get potential raid targets"""
        
        attacker = await session.get(User, attacker_id)
        if not attacker:
            return []
        
        # Find users with similar level (±5 levels)
        level_range = 5
        min_level = max(1, attacker.level - level_range)
        max_level = attacker.level + level_range
        
        # Exclude self and users with active shields
        now = datetime.now()
        
        result = await session.execute(
            select(User).where(
                and_(
                    User.user_id != attacker_id,
                    User.level >= min_level,
                    User.level <= max_level,
                    or_(
                        User.raid_shield_until == None,
                        User.raid_shield_until < now
                    )
                )
            ).order_by(func.random()).limit(limit * 2)  # Get more for filtering
        )
        
        all_targets = list(result.scalars().all())
        
        # Filter out targets on cooldown
        valid_targets = []
        for target in all_targets:
            can_raid, _ = await RaidService.can_raid_target(session, attacker_id, target.user_id)
            if can_raid:
                valid_targets.append(target)
                if len(valid_targets) >= limit:
                    break
        
        return valid_targets
    
    @staticmethod
    async def get_raid_history(
        session: AsyncSession,
        user_id: int,
        limit: int = 20
    ) -> List[Raid]:
        """Get raid history for user"""
        
        result = await session.execute(
            select(Raid).where(
                or_(
                    Raid.attacker_id == user_id,
                    Raid.defender_id == user_id
                )
            ).order_by(Raid.timestamp.desc()).limit(limit)
        )
        
        return list(result.scalars().all())
    
    @staticmethod
    async def get_raid_stats(
        session: AsyncSession,
        user_id: int
    ) -> Dict[str, int]:
        """Get raid statistics for user"""
        
        user = await session.get(User, user_id)
        if not user:
            return {}
        
        return {
            "raids_won": user.raids_won,
            "raids_lost": user.raids_lost,
            "defenses_won": user.defenses_won,
            "defenses_lost": user.defenses_lost,
            "win_rate": round(user.raids_won / max(1, user.raids_won + user.raids_lost) * 100, 1),
            "defense_rate": round(user.defenses_won / max(1, user.defenses_won + user.defenses_lost) * 100, 1),
            "free_raids_today": user.free_raids_today
        }
    
    @staticmethod
    async def buy_trap(
        session: AsyncSession,
        user: User,
        trap_type: str
    ) -> bool:
        """Buy or upgrade a trap"""
        
        trap_data = GameConstants.TRAP_TYPES.get(trap_type)
        if not trap_data:
            raise ValueError("Invalid trap type")
        
        # Get current level
        current_level = user.traps.get(trap_type, 0) if user.traps else 0
        
        # Calculate cost (increases with level)
        cost = trap_data["cost"] * (current_level + 1)
        
        if user.coins < cost:
            raise ValueError(f"Not enough coins. Need: {cost}, have: {user.coins}")
        
        # Deduct coins
        user.coins -= cost
        
        # Upgrade trap
        if not user.traps:
            user.traps = {}
        user.traps[trap_type] = current_level + 1
        
        # Mark as modified for JSON field
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "traps")
        
        await session.commit()
        
        logger.info(f"User {user.user_id} bought/upgraded trap {trap_type} to level {current_level + 1}")
        
        return True
