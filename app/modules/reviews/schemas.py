from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RatingSubmitRequest(BaseModel):
    """Schema for submitting just a 1-5 rating."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")


class ReviewTextSubmitRequest(BaseModel):
    """Schema for submitting just text review."""

    review_text: str = Field(
        ..., min_length=2, description="Text feedback for the service"
    )


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    booking_id: str
    reviewer_id: str
    professional_profile_id: str
    rating: int | None = None
    review_text: str | None = None
    created_at: datetime
    updated_at: datetime


class ReviewListResponse(BaseModel):
    data: list[ReviewResponse]
    total_count: int
