from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.reviews import service
from app.modules.reviews.schemas import (
    RatingSubmitRequest,
    ReviewTextSubmitRequest,
    ReviewResponse,
    ReviewListResponse,
)

review_router = APIRouter(prefix="/reviews", tags=["Reviews"])

@review_router.post("/{booking_id}/rate", response_model=ReviewResponse)
async def submit_rating(
    booking_id: str,
    data: RatingSubmitRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit just a 1-5 star rating for a booking."""
    return await service.upsert_review(
        db=db,
        user_id=current_user.sub,
        booking_id=booking_id,
        rating=data.rating
    )

@review_router.post("/{booking_id}/text", response_model=ReviewResponse)
async def submit_review_text(
    booking_id: str,
    data: ReviewTextSubmitRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit text feedback for a booking."""
    return await service.upsert_review(
        db=db,
        user_id=current_user.sub,
        booking_id=booking_id,
        review_text=data.review_text
    )

@review_router.get("/professional/{profile_id}", response_model=ReviewListResponse)
async def get_professional_reviews(
    profile_id: str,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get a list of reviews for a specific professional."""
    reviews, total = await service.get_reviews_for_professional(
        db=db, professional_profile_id=profile_id, skip=skip, limit=limit
    )
    return {"data": reviews, "total_count": total}
