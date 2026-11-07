from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils.string_utils import StringUtils
from app.modules.booking.models import Booking
from app.modules.professionals.models import ProfessionalProfile
from app.modules.reviews.models import Review


async def update_professional_rating(db: AsyncSession, professional_profile_id: str):
    """
    Recalculates the average_rating and total_reviews for a professional
    and updates their profile.
    """
    # Calculate new average and count
    stats_query = select(
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.rating).label("total_reviews"),
    ).where(
        Review.professional_profile_id == professional_profile_id,
        Review.rating.isnot(None),
    )

    result = await db.execute(stats_query)
    stats = result.first()

    avg_rating = float(stats.avg_rating) if stats and stats.avg_rating else 0.0
    total_reviews = int(stats.total_reviews) if stats and stats.total_reviews else 0

    # Update profile
    prof_query = select(ProfessionalProfile).where(
        ProfessionalProfile.professional_profile_id == professional_profile_id
    )
    prof_result = await db.execute(prof_query)
    professional = prof_result.scalars().first()

    if professional:
        professional.average_rating = round(avg_rating, 1)
        professional.total_reviews = total_reviews
        await db.commit()


async def get_review_by_booking(
    db: AsyncSession, booking_id: str
) -> Review | None:
    """Fetch an existing review for a booking."""
    result = await db.execute(
        select(Review).where(Review.booking_id == booking_id)
    )
    return result.scalars().first()


async def upsert_review(
    db: AsyncSession,
    user_id: str,
    booking_id: str,
    rating: int | None = None,
    review_text: str | None = None,
) -> Review:
    """
    Creates a new review if it doesn't exist, or updates an existing one.
    This supports the "submit rating separately from review text" requirement.
    """
    # Validate booking exists and belongs to user
    booking_query = select(Booking).where(Booking.booking_id == booking_id)
    booking_result = await db.execute(booking_query)
    booking = booking_result.scalars().first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to review this booking."
        )

    review = await get_review_by_booking(db, booking_id)

    if review:
        # Update existing
        if rating is not None:
            review.rating = rating
        if review_text is not None:
            review.review_text = review_text
    else:
        # Create new
        review_id = "RV_" + StringUtils.randomAlphaNumeric(10)
        review = Review(
            review_id=review_id,
            booking_id=booking_id,
            Review=user_id,
            professional_profile_id=booking.professional_profile_id,
            rating=rating,
            review_text=review_text,
        )
        db.add(review)

    await db.commit()
    await db.refresh(review)

    # Recalculate rating if a rating was provided
    if rating is not None:
        await update_professional_rating(db, booking.professional_profile_id)

    return review


async def get_reviews_for_professional(
    db: AsyncSession, professional_profile_id: str, skip: int = 0, limit: int = 10
) -> tuple[list[Review], int]:
    """Gets paginated reviews for a professional."""
    count_query = select(Review).where(
        Review.professional_profile_id == professional_profile_id
    )
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    query = (
        select(Review)
        .where(Review.professional_profile_id == professional_profile_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total
