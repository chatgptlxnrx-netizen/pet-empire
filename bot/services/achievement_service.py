"""
Achievement service - progress tracking and rewards
"""
from typing import List, Optional, Dict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.database.models import Achievement, AchievementProgress, User, Pet
from sqlalchemy import func


class AchievementService:
    """Achievement tracking and rewards"""
    
    @staticmethod
    async def check_and_update_achievements(
        session: AsyncSession,
        user_id: int,
        achievement_type: str,
        value_increment: int = 1
    ) -> List[Achievement]:
        """Check and update achievement progress"""
        
        # Get all achievements of this type
        result = await session.execute(
            select(Achievement).where(
                Achievement.requirement_type == achievement_type
            )
        )
        achievements = result.scalars().all()
        
        newly_completed = []
        
        for achievement in achievements:
            # Get or create progress
            progress_result = await session.execute(
                select(AchievementProgress).where(
                    and_(
                        AchievementProgress.user_id == user_id,
                        AchievementProgress.achievement_id == achievement.id
                    )
                )
            )
            progress = progress_result.scalar_one_or_none()
            
            if not progress:
                progress = AchievementProgress(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    current_value=0
                )
                session.add(progress)
            
            # Skip if already completed
            if progress.completed:
                continue
            
            # Update progress
            progress.current_value += value_increment
            
            # Check completion
            if progress.current_value >= achievement.requirement_value:
                progress.completed = True
                progress.completed_at = func.now()
                
                # Give rewards
                user = await session.get(User, user_id)
                if user:
                    user.coins += achievement.reward_coins
                    user.stars += achievement.reward_stars
                
                newly_completed.append(achievement)
                
                logger.info(f"User {user_id} completed achievement: {achievement.name}")
        
        await session.commit()
        
        return newly_completed
    
    @staticmethod
    async def get_user_achievements(
        session: AsyncSession,
        user_id: int,
        category: Optional[str] = None,
        completed_only: bool = False
    ) -> List[Dict]:
        """Get achievements with progress for user"""
        
        # Build query
        conditions = []
        if category:
            conditions.append(Achievement.category == category)
        
        if conditions:
            achievements_result = await session.execute(
                select(Achievement).where(and_(*conditions)).order_by(Achievement.id)
            )
        else:
            achievements_result = await session.execute(
                select(Achievement).order_by(Achievement.id)
            )
        
        achievements = achievements_result.scalars().all()
        
        result = []
        for achievement in achievements:
            # Get progress
            progress_result = await session.execute(
                select(AchievementProgress).where(
                    and_(
                        AchievementProgress.user_id == user_id,
                        AchievementProgress.achievement_id == achievement.id
                    )
                )
            )
            progress = progress_result.scalar_one_or_none()
            
            # Skip if we want only completed
            if completed_only and (not progress or not progress.completed):
                continue
            
            result.append({
                "achievement": achievement,
                "progress": progress
            })
        
        return result
    
    @staticmethod
    async def get_achievement_stats(
        session: AsyncSession,
        user_id: int
    ) -> Dict:
        """Get achievement statistics"""
        
        # Count total achievements
        total_result = await session.execute(
            select(func.count(Achievement.id))
        )
        total = total_result.scalar()
        
        # Count completed
        completed_result = await session.execute(
            select(func.count(AchievementProgress.id)).where(
                and_(
                    AchievementProgress.user_id == user_id,
                    AchievementProgress.completed == True
                )
            )
        )
        completed = completed_result.scalar()
        
        # Get categories
        categories_result = await session.execute(
            select(Achievement.category, func.count(Achievement.id)).group_by(Achievement.category)
        )
        categories = {row[0]: row[1] for row in categories_result.all()}
        
        return {
            "total": total,
            "completed": completed,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "categories": categories
        }
