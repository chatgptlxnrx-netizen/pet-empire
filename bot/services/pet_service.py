"""
Pet service - business logic for pets
"""
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.database.models import Pet, User
from bot.utils.pet_generator import PetGenerator
from bot.config import GameConstants


class PetService:
    """Pet management service"""
    
    @staticmethod
    async def create_pet(
        session: AsyncSession,
        owner_id: int,
        egg_type: str = "common"
    ) -> Pet:
        """Create a new pet from egg"""
        
        # Generate pet data
        pet_data = PetGenerator.generate_pet(egg_type)
        
        # Create pet in database
        pet = Pet(
            owner_id=owner_id,
            **pet_data
        )
        
        session.add(pet)
        await session.commit()
        await session.refresh(pet)
        
        logger.info(f"Created pet {pet.name} for user {owner_id}")
        
        return pet
    
    @staticmethod
    async def get_user_pets(
        session: AsyncSession,
        user_id: int,
        include_on_mission: bool = True,
        include_defending: bool = True
    ) -> List[Pet]:
        """Get all pets for a user"""
        
        conditions = [Pet.owner_id == user_id]
        
        if not include_on_mission:
            conditions.append(Pet.is_on_mission == False)
        
        if not include_defending:
            conditions.append(Pet.is_defending == False)
        
        result = await session.execute(
            select(Pet).where(and_(*conditions)).order_by(Pet.level.desc(), Pet.rarity.desc())
        )
        
        return list(result.scalars().all())
    
    @staticmethod
    async def get_pet_by_id(
        session: AsyncSession,
        pet_id: int,
        owner_id: Optional[int] = None
    ) -> Optional[Pet]:
        """Get pet by ID, optionally checking owner"""
        
        conditions = [Pet.id == pet_id]
        if owner_id:
            conditions.append(Pet.owner_id == owner_id)
        
        result = await session.execute(
            select(Pet).where(and_(*conditions))
        )
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def add_exp_to_pet(
        session: AsyncSession,
        pet: Pet,
        exp_amount: int
    ) -> Dict[str, any]:
        """Add EXP to pet and handle level ups"""
        
        pet.exp += exp_amount
        levels_gained = 0
        
        # Check for level ups
        while PetGenerator.can_level_up(pet.exp, pet.level) and pet.level < GameConstants.MAX_PET_LEVEL:
            # Level up
            required_exp = PetGenerator.calculate_level_up_requirements(pet.level)
            pet.exp -= required_exp
            pet.level += 1
            levels_gained += 1
            
            # Increase stats
            pet.income_per_hour = int(pet.income_per_hour * 1.05)
            pet.power += 2
            
            # Check evolution
            if pet.level in GameConstants.EVOLUTION_LEVELS:
                pet.evolution_stage += 1
        
        await session.commit()
        await session.refresh(pet)
        
        return {
            "levels_gained": levels_gained,
            "new_level": pet.level,
            "new_power": pet.power,
            "new_income": pet.income_per_hour,
            "evolved": levels_gained > 0 and pet.level in GameConstants.EVOLUTION_LEVELS
        }
    
    @staticmethod
    async def transfer_pet(
        session: AsyncSession,
        pet: Pet,
        new_owner_id: int,
        reason: str = "trade"
    ) -> bool:
        """Transfer pet to new owner"""
        
        try:
            # Check if new owner has slots
            new_owner = await session.get(User, new_owner_id)
            if not new_owner:
                return False
            
            owner_pets_count = await session.scalar(
                select(func.count(Pet.id)).where(Pet.owner_id == new_owner_id)
            )
            
            if owner_pets_count >= new_owner.pet_slots:
                logger.warning(f"User {new_owner_id} has no free pet slots")
                return False
            
            # Reset pet status
            pet.is_on_mission = False
            pet.is_defending = False
            pet.fatigue_until = None
            
            # Transfer ownership
            old_owner_id = pet.owner_id
            pet.owner_id = new_owner_id
            pet.obtained_from = reason
            
            await session.commit()
            
            logger.info(f"Transferred pet {pet.id} from {old_owner_id} to {new_owner_id} ({reason})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer pet: {e}")
            await session.rollback()
            return False
    
    @staticmethod
    async def can_steal_pet(pet: Pet) -> bool:
        """Check if pet can be stolen (based on loyalty)"""
        
        # Mythical pets cannot be stolen
        if pet.rarity == "Mythical":
            return False
        
        # High loyalty reduces steal chance
        if pet.loyalty > 80:
            import random
            return random.random() > GameConstants.LOYALTY_STEAL_REDUCTION
        
        return True
    
    @staticmethod
    async def get_available_pets_for_mission(
        session: AsyncSession,
        user_id: int
    ) -> List[Pet]:
        """Get pets available for missions"""
        
        now = datetime.now()
        
        result = await session.execute(
            select(Pet).where(
                and_(
                    Pet.owner_id == user_id,
                    Pet.is_on_mission == False,
                    Pet.is_defending == False,
                    or_(
                        Pet.fatigue_until == None,
                        Pet.fatigue_until < now
                    )
                )
            ).order_by(Pet.power.desc())
        )
        
        return list(result.scalars().all())
    
    @staticmethod
    async def get_available_pets_for_raid(
        session: AsyncSession,
        user_id: int,
        max_count: int = 5
    ) -> List[Pet]:
        """Get pets available for raids"""
        
        now = datetime.now()
        
        result = await session.execute(
            select(Pet).where(
                and_(
                    Pet.owner_id == user_id,
                    Pet.is_on_mission == False,
                    or_(
                        Pet.fatigue_until == None,
                        Pet.fatigue_until < now
                    )
                )
            ).order_by(Pet.power.desc()).limit(max_count)
        )
        
        return list(result.scalars().all())
    
    @staticmethod
    async def set_pet_fatigue(
        session: AsyncSession,
        pet: Pet,
        hours: int = 2
    ):
        """Set pet fatigue for specified hours"""
        from datetime import timedelta
        
        pet.fatigue_until = datetime.now() + timedelta(hours=hours)
        await session.commit()
    
    @staticmethod
    async def calculate_total_defense_power(
        session: AsyncSession,
        user_id: int
    ) -> int:
        """Calculate total defense power for user"""
        
        # Get defending pets
        result = await session.execute(
            select(Pet).where(
                and_(
                    Pet.owner_id == user_id,
                    Pet.is_defending == True
                )
            )
        )
        defending_pets = result.scalars().all()
        
        # Calculate base power
        total_power = sum(pet.power * pet.level for pet in defending_pets)
        
        # Add trap bonuses
        user = await session.get(User, user_id)
        if user and user.traps:
            for trap_type, level in user.traps.items():
                trap_data = GameConstants.TRAP_TYPES.get(trap_type, {})
                bonus = trap_data.get("defense_bonus", 0) * level
                total_power += bonus
        
        return total_power
    
    @staticmethod
    async def get_stealable_pets(
        session: AsyncSession,
        user_id: int
    ) -> List[Pet]:
        """Get pets that can be stolen from user"""
        
        result = await session.execute(
            select(Pet).where(
                and_(
                    Pet.owner_id == user_id,
                    Pet.is_on_mission == False,
                    Pet.rarity != "Mythical"  # Mythical can't be stolen
                )
            )
        )
        
        return list(result.scalars().all())
    
    @staticmethod
    async def count_pets_by_rarity(
        session: AsyncSession,
        user_id: int
    ) -> Dict[str, int]:
        """Count pets by rarity for user"""
        
        result = await session.execute(
            select(Pet.rarity, func.count(Pet.id)).where(
                Pet.owner_id == user_id
            ).group_by(Pet.rarity)
        )
        
        counts = {row[0]: row[1] for row in result.all()}
        
        # Fill in missing rarities with 0
        for rarity in GameConstants.RARITIES.keys():
            if rarity not in counts:
                counts[rarity] = 0
        
        return counts
    
    @staticmethod
    async def get_total_collection_value(
        session: AsyncSession,
        user_id: int
    ) -> int:
        """Calculate total value of user's pet collection"""
        
        pets = await PetService.get_user_pets(session, user_id)
        
        total_value = sum(
            PetGenerator.calculate_pet_value(
                pet.rarity,
                pet.level,
                pet.is_shiny
            )
            for pet in pets
        )
        
        return total_value


# Need to import or_ after defining the class
from sqlalchemy import or_
