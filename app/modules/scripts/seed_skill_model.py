import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# import models to ensure they're registered with SQLAlchemy
from app.modules.auth.models import Authorization, Role
from app.modules.users.models import User
from app.modules.file.models import File
from app.modules.professional_applications.models import ProfessionalApplication  # noqa: F401
from app.modules.professionals.models import ProfessionalProfile
from app.modules.skills.models import Skill

from app.core.db.database import AsyncSessionLocal

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
    # Fetch existing skill names using IN clause
    result = await db.execute(select(Skill.name).where(Skill.name.in_(DEFAULT_SKILLS)))
    existing_skill_names = set(result.scalars().all())

    # Determine skills to add based on existing skills
    if not existing_skill_names:
        skills_to_add = DEFAULT_SKILLS
    else:
        skills_to_add = [name for name in DEFAULT_SKILLS if name not in existing_skill_names]

    # Store skills in database
    if skills_to_add:
        new_skill_objects = [Skill(name=name) for name in skills_to_add]
        db.add_all(new_skill_objects)
        await db.commit()
        print(f"[SUCCESS] Seeded {len(skills_to_add)} new skills successfully.")
    else:
        print("[INFO] All default skills already exist in database.")


async def main():
    async with AsyncSessionLocal() as db:
        await seed_skills(db)


if __name__ == "__main__":
    asyncio.run(main())
