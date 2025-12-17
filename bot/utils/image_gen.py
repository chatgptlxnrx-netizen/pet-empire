"""
Image generation utilities for pet cards
"""
import io
from typing import Optional
from PIL import Image, ImageDraw, ImageFont


class ImageGenerator:
    """Generate images for pets and cards"""
    
    # Color schemes by rarity
    RARITY_COLORS = {
        "Common": {
            "bg": (200, 200, 200),
            "border": (150, 150, 150),
            "text": (50, 50, 50)
        },
        "Uncommon": {
            "bg": (144, 238, 144),
            "border": (34, 139, 34),
            "text": (0, 50, 0)
        },
        "Rare": {
            "bg": (135, 206, 250),
            "border": (30, 144, 255),
            "text": (0, 0, 139)
        },
        "Epic": {
            "bg": (216, 191, 216),
            "border": (138, 43, 226),
            "text": (75, 0, 130)
        },
        "Legendary": {
            "bg": (255, 215, 0),
            "border": (218, 165, 32),
            "text": (139, 69, 19)
        },
        "Mythical": {
            "bg": (255, 182, 193),
            "border": (255, 20, 147),
            "text": (139, 0, 139)
        }
    }
    
    @staticmethod
    def generate_pet_card(
        pet_data: dict,
        width: int = 400,
        height: int = 500
    ) -> io.BytesIO:
        """Generate a pet card image"""
        
        # Get rarity colors
        rarity = pet_data.get("rarity", "Common")
        colors = ImageGenerator.RARITY_COLORS.get(rarity, ImageGenerator.RARITY_COLORS["Common"])
        
        # Create image
        img = Image.new('RGB', (width, height), color=colors["bg"])
        draw = ImageDraw.Draw(img)
        
        # Draw border
        border_width = 10
        draw.rectangle(
            [0, 0, width-1, height-1],
            outline=colors["border"],
            width=border_width
        )
        
        # Try to load font, fallback to default
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw content
        y_offset = 30
        
        # Pet emoji (large)
        emoji_text = pet_data.get("emoji", "🐾")
        emoji_bbox = draw.textbbox((0, 0), emoji_text, font=title_font)
        emoji_width = emoji_bbox[2] - emoji_bbox[0]
        draw.text(
            ((width - emoji_width) // 2, y_offset),
            emoji_text,
            fill=colors["text"],
            font=title_font
        )
        y_offset += 80
        
        # Pet name
        name = pet_data.get("name", "Unknown Pet")
        name_bbox = draw.textbbox((0, 0), name, font=title_font)
        name_width = name_bbox[2] - name_bbox[0]
        draw.text(
            ((width - name_width) // 2, y_offset),
            name,
            fill=colors["text"],
            font=title_font
        )
        y_offset += 50
        
        # Rarity badge
        rarity_text = f"★ {rarity} ★"
        rarity_bbox = draw.textbbox((0, 0), rarity_text, font=text_font)
        rarity_width = rarity_bbox[2] - rarity_bbox[0]
        
        # Draw rarity background
        padding = 10
        draw.rectangle(
            [
                (width - rarity_width) // 2 - padding,
                y_offset - 5,
                (width - rarity_width) // 2 + rarity_width + padding,
                y_offset + 30
            ],
            fill=colors["border"]
        )
        
        draw.text(
            ((width - rarity_width) // 2, y_offset),
            rarity_text,
            fill=(255, 255, 255),
            font=text_font
        )
        y_offset += 60
        
        # Stats
        stats = [
            f"Level: {pet_data.get('level', 1)}",
            f"Power: {pet_data.get('power', 0)}",
            f"Income: {pet_data.get('income_per_hour', 0)}/h",
            f"Loyalty: {pet_data.get('loyalty', 50)}%"
        ]
        
        for stat in stats:
            stat_bbox = draw.textbbox((0, 0), stat, font=text_font)
            stat_width = stat_bbox[2] - stat_bbox[0]
            draw.text(
                ((width - stat_width) // 2, y_offset),
                stat,
                fill=colors["text"],
                font=text_font
            )
            y_offset += 35
        
        # Shiny indicator
        if pet_data.get("is_shiny"):
            shiny_text = "✨ SHINY ✨"
            shiny_bbox = draw.textbbox((0, 0), shiny_text, font=text_font)
            shiny_width = shiny_bbox[2] - shiny_bbox[0]
            draw.text(
                ((width - shiny_width) // 2, y_offset),
                shiny_text,
                fill=(255, 215, 0),
                font=text_font
            )
        
        # Convert to bytes
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        
        return bio
    
    @staticmethod
    def generate_achievement_badge(
        achievement_data: dict,
        size: int = 300
    ) -> io.BytesIO:
        """Generate achievement badge image"""
        
        # Create circular badge
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw circle
        circle_color = (255, 215, 0) if achievement_data.get("completed") else (150, 150, 150)
        draw.ellipse([10, 10, size-10, size-10], fill=circle_color, outline=(218, 165, 32), width=5)
        
        # Try to load font
        try:
            icon_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            icon_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Draw icon
        icon = achievement_data.get("icon", "🏆")
        icon_bbox = draw.textbbox((0, 0), icon, font=icon_font)
        icon_width = icon_bbox[2] - icon_bbox[0]
        icon_height = icon_bbox[3] - icon_bbox[1]
        draw.text(
            ((size - icon_width) // 2, (size - icon_height) // 2 - 40),
            icon,
            fill=(255, 255, 255),
            font=icon_font
        )
        
        # Draw name (wrapped)
        name = achievement_data.get("name", "Achievement")
        name_bbox = draw.textbbox((0, 0), name, font=text_font)
        name_width = name_bbox[2] - name_bbox[0]
        draw.text(
            ((size - name_width) // 2, size - 80),
            name,
            fill=(255, 255, 255),
            font=text_font
        )
        
        # Convert to bytes
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        
        return bio
    
    @staticmethod
    def generate_egg_image(egg_type: str = "common") -> io.BytesIO:
        """Generate egg image"""
        
        egg_colors = {
            "common": (200, 200, 200),
            "rare": (135, 206, 250),
            "epic": (216, 191, 216),
            "legendary": (255, 215, 0),
            "mythical": (255, 105, 180)
        }
        
        color = egg_colors.get(egg_type, egg_colors["common"])
        
        # Create image
        size = 300
        img = Image.new('RGB', (size, size), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw egg shape (ellipse)
        margin = 30
        draw.ellipse(
            [margin, margin // 2, size-margin, size-margin],
            fill=color,
            outline=(0, 0, 0),
            width=5
        )
        
        # Add decorative spots
        spot_color = tuple(max(0, c - 40) for c in color)
        for _ in range(5):
            import random
            x = random.randint(margin + 20, size - margin - 40)
            y = random.randint(margin + 20, size - margin - 40)
            spot_size = random.randint(10, 25)
            draw.ellipse(
                [x, y, x + spot_size, y + spot_size],
                fill=spot_color
            )
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        text = egg_type.upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((size - text_width) // 2, size // 2),
            text,
            fill=(255, 255, 255),
            font=font,
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )
        
        # Convert to bytes
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        
        return bio
