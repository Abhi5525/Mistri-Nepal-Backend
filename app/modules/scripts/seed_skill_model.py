import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# import models to ensure they're registered with SQLAlchemy
from app.modules.auth.models import Authorization, Role
from app.modules.users.models import User
from app.modules.file.models import File
from app.modules.professional_applications.models import ProfessionalApplication  # noqa: F401
from app.modules.professionals.models import ProfessionalProfile
from app.modules.skills.models import Skill  # noqa: F401

from app.core.db.database import AsyncSessionLocal
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
    added_count = 0
    for name in DEFAULT_SKILLS:
        result = await db.execute(select(Skill).where(Skill.name == name))
        exists = result.scalar_one_or_none()

        if not exists:
            db.add(Skill(name=name))
            added_count += 1

    if added_count > 0:
        await db.commit()
        print(f"[SUCCESS] Seeded {added_count} new skills successfully.")
    else:
        print("[INFO] All default skills already exist in database.")


async def main():
    async with AsyncSessionLocal() as db:
        await seed_skills(db)


if __name__ == "__main__":
    asyncio.run(main())
