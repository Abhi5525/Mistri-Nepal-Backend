from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.core.security.security import get_current_user
from app.modules.auth.schemas import JwtPayload
from app.modules.users import service
from app.modules.users.schemas import (
    UserResponse,
    UserDetailResponse,
    UserUpdate,
    PasswordChangeRequest,
    PasswordChangeResponse,
    FcmTokenUpdateRequest,
    FcmTokenUpdateResponse,
    UserListResponse,
    UserSearchResponse,
    AccountDeletionRequest,
    AccountDeletionResponse,
)
from app.common.enum.role_enum import RoleEnum

user_router = APIRouter(prefix="/users", tags=["User Management"])


# ✅ GET CURRENT USER PROFILE
@user_router.get("/me", response_model=UserDetailResponse)
async def get_current_user_profile(
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user's profile"""
    user = await service.get_user_with_details(db=db, user_id=current_user.sub)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# ✅ UPDATE CURRENT USER PROFILE
@user_router.put("/me", response_model=UserDetailResponse)
async def update_current_user_profile(
    data: UserUpdate,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile"""
    user = await service.update_user_profile(
        db=db,
        user_id=current_user.sub,
        full_name=data.full_name,
        email=data.email,
    )
    
    return user


# ✅ CHANGE PASSWORD
@user_router.post("/me/change-password", response_model=PasswordChangeResponse)
async def change_password(
    data: PasswordChangeRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password"""
    await service.change_password(
        db=db,
        user_id=current_user.sub,
        old_password=data.old_password,
        new_password=data.new_password,
    )
    
    return PasswordChangeResponse()


# ✅ UPDATE FCM TOKEN
@user_router.post("/me/fcm-token", response_model=FcmTokenUpdateResponse)
async def update_fcm_token(
    data: FcmTokenUpdateRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update FCM token for push notifications"""
    await service.update_fcm_token(
        db=db,
        user_id=current_user.sub,
        fcm_token=data.fcm_token,
    )
    
    return FcmTokenUpdateResponse()


# ✅ DELETE ACCOUNT
@user_router.delete("/me", response_model=AccountDeletionResponse)
async def delete_account(
    data: AccountDeletionRequest,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete current user's account"""
    # Verify password before deletion
    user_by_phone = await service.get_user_by_phone_number(db=db, phone_number=current_user.sub)
    
    from app.core.security.security import verify_password
    if not user_by_phone or not verify_password(data.password, user_by_phone.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    await service.delete_user_account(db=db, user_id=current_user.sub)
    
    return AccountDeletionResponse()


# ✅ GET USER BY ID (ADMIN)
@user_router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_by_id(
    user_id: str,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view other user profiles")
    
    user = await service.get_user_with_details(db=db, user_id=user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# ✅ SEARCH USERS (ADMIN)
@user_router.get("/search", response_model=UserSearchResponse)
async def search_users(
    query: str = None,
    skip: int = 0,
    limit: int = 10,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search users by phone number, name, or email (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can search users")
    
    results = await service.search_users(
        db=db,
        query=query,
        skip=skip,
        limit=limit,
    )
    
    return UserSearchResponse(results=results, total=len(results))


# ✅ GET ALL USERS (ADMIN)
@user_router.get("/admin/all", response_model=UserListResponse)
async def get_all_users(
    skip: int = 0,
    limit: int = 10,
    current_user: JwtPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all users with pagination (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view all users")
    
    users = await service.get_all_users(db=db, skip=skip, limit=limit)
    
    return UserListResponse(users=users, total=len(users), skip=skip, limit=limit)
