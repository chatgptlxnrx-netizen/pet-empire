"""
Pet generation utilities
"""
import random
from datetime import datetime
from typing import Dict, Optional

from bot.config import GameConstants


# Pet emojis by type
PET_EMOJIS = {
    # Common pets
    "Cat": "🐱",
    "Dog": "🐶",
    "Hamster": "🐹",
    "Parrot": "🦜",
    "Rabbit": "🐰",
    
    # Fantasy pets
    "Dragon": "🐉",
    "Unicorn": "🦄",
    "Phoenix": "🔥",
    "Griffin": "🦅",
    "Pegasus": "🐴",
    
    # Meme pets
    "Doge": "🐕",
    "Pepe": "🐸",
    "Shiba": "🐕",
    "Cheems": "🐶",
    "Wojak": "😐",
    
    # Mythical pets
    "Cerberus": "🐺",
    "Hydra": "🐍",
    "Kraken": "🦑",
    "Basilisk": "🐍",
    "Manticore": "🦁"
}


# Pet name prefixes by rarity
NAME_PREFIXES = {
    "Common": ["Little", "Tiny", "Small", "Young", "Baby"],
    "Uncommon": ["Swift", "Quick", "Brave", "Bold", "Strong"],
    "Rare": ["Noble", "Mighty", "Fierce", "Royal", "Grand"],
    "Epic": ["Ancient", "Legendary", "Mystic", "Celestial", "Divine"],
    "Legendary": ["Supreme", "Immortal", "Eternal", "Cosmic", "Radiant"],
    "Mythical": ["Transcendent", "Omnipotent", "Primordial", "Infinite", "Ultimate"]
}


class PetGenerator:
    """Pet generation and management"""
    
    @staticmethod
    def determine_rarity(egg_type: str = "common") -> str:
        """Determine pet rarity based on egg type and random chance"""
        
        if egg_type == "mythical":
            return "Mythical"
        elif egg_type == "legendary":
            rarities = ["Legendary", "Mythical"]
            weights = [0.9, 0.1]
            return random.choices(rarities, weights=weights)[0]
        elif egg_type == "epic":
            rarities = ["Epic", "Legendary"]
            weights = [0.8, 0.2]
            return random.choices(rarities, weights=weights)[0]
        elif egg_type == "rare":
            rarities = ["Rare", "Epic", "Legendary"]
            weights = [0.7, 0.25, 0.05]
            return random.choices(rarities, weights=weights)[0]
        else:  # common egg
            rarities = list(GameConstants.RARITIES.keys())
            weights = [GameConstants.RARITIES[r]["chance"] for r in rarities]
            return random.choices(rarities, weights=weights)[0]
    
    @staticmethod
    def generate_pet_name(pet_type: str, rarity: str) -> str:
        """Generate a name for the pet"""
        prefix = random.choice(NAME_PREFIXES[rarity])
        return f"{prefix} {pet_type}"
    
    @staticmethod
    def calculate_base_stats(rarity: str, is_shiny: bool = False) -> Dict[str, int]:
        """Calculate base stats for pet based on rarity"""
        rarity_data = GameConstants.RARITIES[rarity]
        
        base_income = rarity_data["base_income"]
        base_power = rarity_data["base_power"]
        
        # Shiny bonus: +20% to all stats
        if is_shiny:
            base_income = int(base_income * 1.2)
            base_power = int(base_power * 1.2)
        
        return {
            "income_per_hour": base_income,
            "power": base_power,
            "stamina": 100,
            "loyalty": random.randint(40, 60)
        }
    
    @staticmethod
    def is_shiny() -> bool:
        """Determine if pet is shiny (1% chance)"""
        return random.random() < 0.01
    
    @staticmethod
    def generate_pet(
        egg_type: str = "common",
        pet_type: Optional[str] = None
    ) -> Dict:
        """Generate a complete pet with all attributes"""
        
        # Determine rarity
        rarity = PetGenerator.determine_rarity(egg_type)
        
        # Determine if shiny
        is_shiny = PetGenerator.is_shiny()
        
        # Select pet type if not specified
        if not pet_type:
            # Higher rarities more likely to get fantasy/mythical pets
            if rarity in ["Mythical", "Legendary"]:
                pet_type = random.choice(GameConstants.PET_TYPES[10:])
            elif rarity in ["Epic", "Rare"]:
                pet_type = random.choice(GameConstants.PET_TYPES[5:15])
            else:
                pet_type = random.choice(GameConstants.PET_TYPES[:10])
        
        # Generate name
        name = PetGenerator.generate_pet_name(pet_type, rarity)
        
        # Get emoji
        emoji = PET_EMOJIS.get(pet_type, "🐾")
        
        # Calculate stats
        stats = PetGenerator.calculate_base_stats(rarity, is_shiny)
        
        return {
            "name": name,
            "pet_type": pet_type,
            "rarity": rarity,
            "emoji": emoji,
            "level": 1,
            "exp": 0,
            "power": stats["power"],
            "income_per_hour": stats["income_per_hour"],
            "stamina": stats["stamina"],
            "loyalty": stats["loyalty"],
            "is_shiny": is_shiny,
            "evolution_stage": 0,
            "obtained_from": "egg"
        }
    
    @staticmethod
    def calculate_level_up_requirements(current_level: int) -> int:
        """Calculate EXP required for next level"""
        # Formula: 100 * (1.1 ^ level)
        return int(GameConstants.EXP_PER_LEVEL * (1.1 ** current_level))
    
    @staticmethod
    def can_level_up(current_exp: int, current_level: int) -> bool:
        """Check if pet can level up"""
        required_exp = PetGenerator.calculate_level_up_requirements(current_level)
        return current_exp >= required_exp
    
    @staticmethod
    def level_up_pet(pet_data: Dict) -> Dict:
        """Level up a pet and recalculate stats"""
        pet_data["level"] += 1
        pet_data["exp"] -= PetGenerator.calculate_level_up_requirements(pet_data["level"] - 1)
        
        # Increase stats: +5% income, +2 power per level
        pet_data["income_per_hour"] = int(pet_data["income_per_hour"] * 1.05)
        pet_data["power"] += 2
        
        # Check for evolution
        if pet_data["level"] in GameConstants.EVOLUTION_LEVELS:
            pet_data["evolution_stage"] += 1
        
        return pet_data
    
    @staticmethod
    def calculate_pet_value(
        rarity: str,
        level: int,
        is_shiny: bool = False
    ) -> int:
        """Calculate total value of a pet"""
        base_values = {
            "Common": 100,
            "Uncommon": 300,
            "Rare": 800,
            "Epic": 2500,
            "Legendary": 10000,
            "Mythical": 50000
        }
        
        base_value = base_values.get(rarity, 100)
        level_multiplier = 1 + (level * 0.1)
        shiny_multiplier = 2.0 if is_shiny else 1.0
        
        return int(base_value * level_multiplier * shiny_multiplier)
    
    @staticmethod
    def generate_mission_rewards(
        mission_type: str,
        pet_level: int,
        pet_rarity: str
    ) -> Dict[str, int]:
        """Calculate mission rewards based on pet stats"""
        mission_data = GameConstants.MISSION_TYPES[mission_type]
        
        # Base rewards
        base_coins = mission_data["base_reward"]
        base_exp = mission_data["exp_reward"]
        
        # Level multiplier (higher level = better rewards)
        level_multiplier = 1 + (pet_level * 0.05)
        
        # Rarity bonus
        rarity_bonus = {
            "Common": 1.0,
            "Uncommon": 1.2,
            "Rare": 1.5,
            "Epic": 2.0,
            "Legendary": 3.0,
            "Mythical": 5.0
        }
        
        multiplier = level_multiplier * rarity_bonus.get(pet_rarity, 1.0)
        
        return {
            "coins": int(base_coins * multiplier),
            "exp": int(base_exp * multiplier)
        }
    
    @staticmethod
    def calculate_mission_success_chance(
        pet_stamina: int,
        pet_level: int,
        mission_type: str
    ) -> float:
        """Calculate chance of mission success"""
        base_fail_chance = GameConstants.MISSION_TYPES[mission_type]["fail_chance"]
        
        # Stamina affects success (below 50 stamina = higher fail rate)
        stamina_modifier = 1.0 if pet_stamina >= 50 else (pet_stamina / 50)
        
        # Level reduces fail chance
        level_modifier = 1.0 - (pet_level * 0.005)  # -0.5% per level
        level_modifier = max(0.5, level_modifier)  # Minimum 50% of base fail rate
        
        final_fail_chance = base_fail_chance * level_modifier * (2 - stamina_modifier)
        success_chance = 1.0 - min(final_fail_chance, 0.5)  # Max 50% fail rate
        
        return success_chance


# Mission name generator
MISSION_NAMES = {
    "quick": [
        "🌳 Walk in the Park",
        "🦴 Find a Treat",
        "🏃 Quick Run",
        "🎾 Play Fetch",
        "🌸 Flower Picking"
    ],
    "medium": [
        "💎 Treasure Hunt",
        "🏠 Guard the House",
        "🎣 Fishing Trip",
        "🗺️ Explore Forest",
        "⚔️ Train in Arena"
    ],
    "long": [
        "🏰 Dungeon Expedition",
        "🛡️ Guard Caravan",
        "⛰️ Mountain Climb",
        "🌊 Deep Sea Dive",
        "🔮 Ancient Ruins"
    ],
    "epic": [
        "🐉 Dragon's Lair",
        "👑 Rescue the Princess",
        "💀 Defeat the Boss",
        "🌟 Cosmic Journey",
        "⚡ Storm the Castle"
    ]
}


def get_random_mission_name(mission_type: str) -> str:
    """Get a random mission name for the mission type"""
    return random.choice(MISSION_NAMES.get(mission_type, ["Unknown Mission"]))
