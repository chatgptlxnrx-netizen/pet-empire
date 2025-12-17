"""
Mission service - idle mission mechanics
"""
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.database.models import Mission, Pet, User
from bot.utils.pet_generator import PetGenerator, get_random_mission_name
from bot.config import GameConstants


class MissionService:
    """Mission management service"""
    
    @staticmethod
    async def start_mission(
        session: AsyncSession,
        pet: Pet,
        mission_type: str
    ) -> Mission:
        """Start a new mission for a pet"""
        
        if pet.is_on_mission:
            raise ValueError("Pet is already on a mission")
        
        if pet.is_defending:
            raise ValueError("Pet is currently defending")
        
        # Check fatigue
        if pet.fatigue_until and pet.fatigue_until > datetime.now():
            raise ValueError("Pet is too tired")
        
        # Get mission data
        mission_data = GameConstants.MISSION_TYPES.get(mission_type)
        if not mission_data:
            raise ValueError("Invalid mission type")
        
        # Calculate rewards
        rewards = PetGenerator.generate_mission_rewards(
            mission_type,
            pet.level,
            pet.rarity
        )
        
        # Create mission
        now = datetime.now()
        complete_at = now + timedelta(seconds=mission_data["duration"])
        
        mission = Mission(
            user_id=pet.owner_id,
            pet_id=pet.id,
            mission_type=mission_type,
            mission_name=get_random_mission_name(mission_type),
            started_at=now,
            complete_at=complete_at,
            reward_coins=rewards["coins"],
            reward_exp=rewards["exp"],
            status="active"
        )
        
        # Update pet status
        pet.is_on_mission = True
        
        session.add(mission)
        await session.commit()
        await session.refresh(mission)
        
        logger.info(f"Started mission {mission.id} for pet {pet.id}")
        
        return mission
    
    @staticmethod
    async def complete_mission(
        session: AsyncSession,
        mission: Mission
    ) -> Dict[str, any]:
        """Complete a mission and give rewards"""
        
        if mission.status != "active":
            raise ValueError("Mission is not active")
        
        if mission.complete_at > datetime.now():
            raise ValueError("Mission is not complete yet")
        
        # Get pet
        pet = await session.get(Pet, mission.pet_id)
        if not pet:
            raise ValueError("Pet not found")
        
        # Calculate success
        success_chance = PetGenerator.calculate_mission_success_chance(
            pet.stamina,
            pet.level,
            mission.mission_type
        )
        
        success = random.random() < success_chance
        
        if success:
            # Give full rewards
            user = await session.get(User, mission.user_id)
            user.coins += mission.reward_coins
            user.exp += mission.reward_exp // 10  # 10% of mission exp goes to user
            
            # Give EXP to pet
            from bot.services.pet_service import PetService
            level_up_info = await PetService.add_exp_to_pet(
                session,
                pet,
                mission.reward_exp
            )
            
            mission.status = "completed"
            result = {
                "success": True,
                "coins": mission.reward_coins,
                "exp": mission.reward_exp,
                "level_up_info": level_up_info
            }
            
            logger.info(f"Mission {mission.id} completed successfully")
            
        else:
            # Failed - reduced rewards and fatigue
            reduced_coins = int(mission.reward_coins * 0.2)
            user = await session.get(User, mission.user_id)
            user.coins += reduced_coins
            
            # Set fatigue
            pet.fatigue_until = datetime.now() + timedelta(hours=1)
            
            mission.status = "failed"
            result = {
                "success": False,
                "coins": reduced_coins,
                "exp": 0,
                "level_up_info": {"levels_gained": 0}
            }
            
            logger.info(f"Mission {mission.id} failed")
        
        # Update pet status
        pet.is_on_mission = False
        
        await session.commit()
        
        return result
    
    @staticmethod
    async def get_user_missions(
        session: AsyncSession,
        user_id: int,
        status: Optional[str] = None
    ) -> List[Mission]:
        """Get missions for user"""
        
        conditions = [Mission.user_id == user_id]
        if status:
            conditions.append(Mission.status == status)
        
        result = await session.execute(
            select(Mission).where(and_(*conditions)).order_by(Mission.complete_at.desc())
        )
        
        return list(result.scalars().all())
    
    @staticmethod
    async def get_active_missions(
        session: AsyncSession,
        user_id: int
    ) -> List[Mission]:
        """Get all active missions for user"""
        return await MissionService.get_user_missions(session, user_id, "active")
    
    @staticmethod
    async def get_completed_missions(
        session: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[Mission]:
        """Get recently completed missions"""
        
        result = await session.execute(
            select(Mission).where(
                and_(
                    Mission.user_id == user_id,
                    Mission.status.in_(["completed", "failed"])
                )
            ).order_by(Mission.complete_at.desc()).limit(limit)
        )
        
        return list(result.scalars().all())
    
    @staticmethod
    async def get_mission_by_pet(
        session: AsyncSession,
        pet_id: int
    ) -> Optional[Mission]:
        """Get active mission for a pet"""
        
        result = await session.execute(
            select(Mission).where(
                and_(
                    Mission.pet_id == pet_id,
                    Mission.status == "active"
                )
            )
        )
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def cancel_mission(
        session: AsyncSession,
        mission: Mission
    ) -> bool:
        """Cancel an active mission (with penalty)"""
        
        if mission.status != "active":
            return False
        
        # Get pet
        pet = await session.get(Pet, mission.pet_id)
        if pet:
            pet.is_on_mission = False
            # Penalty: 1 hour fatigue
            pet.fatigue_until = datetime.now() + timedelta(hours=1)
        
        mission.status = "cancelled"
        await session.commit()
        
        logger.info(f"Cancelled mission {mission.id}")
        
        return True
    
    @staticmethod
    async def instant_complete_mission(
        session: AsyncSession,
        mission: Mission,
        user: User
    ) -> Dict[str, any]:
        """Instantly complete mission for Stars"""
        
        if mission.status != "active":
            raise ValueError("Mission is not active")
        
        # Calculate cost based on time remaining
        time_left = mission.complete_at - datetime.now()
        hours_left = time_left.total_seconds() / 3600
        cost = max(20, int(hours_left * 10))  # 10 Stars per hour, minimum 20
        
        if user.stars < cost:
            raise ValueError("Not enough Stars")
        
        # Deduct Stars
        user.stars -= cost
        
        # Set mission as ready to collect
        mission.complete_at = datetime.now()
        
        await session.commit()
        
        logger.info(f"Instantly completed mission {mission.id} for {cost} Stars")
        
        return {
            "cost": cost,
            "mission": mission
        }
    
    @staticmethod
    async def check_and_autocomplete_missions(
        session: AsyncSession
    ):
        """Background task: auto-complete ready missions"""
        
        now = datetime.now()
        
        # Find all ready missions
        result = await session.execute(
            select(Mission).where(
                and_(
                    Mission.status == "active",
                    Mission.complete_at <= now
                )
            )
        )
        
        missions = result.scalars().all()
        
        for mission in missions:
            try:
                await MissionService.complete_mission(session, mission)
            except Exception as e:
                logger.error(f"Failed to auto-complete mission {mission.id}: {e}")
        
        logger.info(f"Auto-completed {len(missions)} missions")
