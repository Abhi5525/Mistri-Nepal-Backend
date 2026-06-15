from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.skills.models import Skill

DEFAULT_SKILLS = [
    # 🏠 Core Home Repair
    "Plumbing",
    "Electrical Work",
    "Carpentry",
    "Painting",
    "General Handyman",
    "Appliance Repair",

    # ❄️ HVAC / Mechanical
    "HVAC Installation",
    "Air Conditioning Repair",
    "Heating System Repair",
    "Ventilation Services",
    "Refrigerator Repair",

    # 🧹 Cleaning Services
    "House Cleaning",
    "Deep Cleaning",
    "Office Cleaning",
    "Carpet Cleaning",
    "Window Cleaning",
    "Pest Control",

    # 🏗️ Construction / Installation
    "Masonry Work",
    "Tiling",
    "Flooring Installation",
    "Drywall Installation",
    "Roof Repair",
    "Waterproofing",

    # 🌿 Outdoor / Garden
    "Gardening",
    "Lawn Care",
    "Landscaping",
    "Tree Cutting",
    "Irrigation Setup",
    "Fence Installation",

    # 🔐 Security / Tech Home Setup
    "CCTV Installation",
    "Home Security Systems",
    "Smart Home Setup",
    "WiFi & Networking Setup",
    "Solar Panel Installation",

    # 🚗 Transport / Misc Services
    "Moving Services",
    "Furniture Assembly",
    "Locksmith",
    "Interior Decoration",
]

async def seed_skills(db: AsyncSession):
    for name in DEFAULT_SKILLS:
        result = await db.execute(
            select(Skill).where(Skill.name == name)
        )
        exists = result.scalar_one_or_none()

        if not exists:
            db.add(Skill(name=name))

    await db.commit()