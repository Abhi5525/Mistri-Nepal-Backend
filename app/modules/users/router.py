from fastapi import APIRouter, Depends, HTTPException

from app.common.enum.role_enum import RoleEnum
from app.core.security.security import get_current_user, verify_password
from app.modules.auth.schemas import JwtPayload
from app.modules.users.dependencies import get_user_service
from app.modules.users.schemas import (
    AccountDeletionRequest,
    AccountDeletionResponse,
    FcmTokenUpdateRequest,
    FcmTokenUpdateResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    UserDetailResponse,
    UserListResponse,
    UserSearchResponse,
    UserUpdate,
)

# Import the class instead of the module
from app.modules.users.service import UserService

user_router = APIRouter(prefix="/users", tags=["User Management"])


# ✅ GET CURRENT USER PROFILE
@user_router.get("/me", response_model=UserDetailResponse)
async def get_current_user_profile(
    current_user: JwtPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get current authenticated user's profile"""
    user = await user_service.get_user_with_details(user_id=current_user.sub)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ✅ UPDATE CURRENT USER PROFILE
@user_router.put("/me", response_model=UserDetailResponse)
async def update_current_user_profile(
    data: UserUpdate,
    current_user: JwtPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update current user's profile"""
    user = await user_service.update_user_profile(
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
    user_service: UserService = Depends(get_user_service),
):
    """Change current user's password"""
    await user_service.change_password(
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
    user_service: UserService = Depends(get_user_service),
):
    """Update FCM token for push notifications"""
    await user_service.update_fcm_token(
        user_id=current_user.sub,
        fcm_token=data.fcm_token,
    )

    return FcmTokenUpdateResponse()


# ✅ DELETE ACCOUNT
@user_router.delete("/me", response_model=AccountDeletionResponse)
async def delete_account(
    data: AccountDeletionRequest,
    current_user: JwtPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Delete current user's account"""
    # Verify password before deletion
    user_by_phone = await user_service.get_user_by_phone_number(
        phone_number=current_user.sub
    )

    if not user_by_phone or not verify_password(data.password, user_by_phone.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    await user_service.delete_user_account(user_id=current_user.sub)

    return AccountDeletionResponse()


# ✅ GET USER BY ID (ADMIN)
@user_router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_by_id(
    user_id: str,
    current_user: JwtPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get user by ID (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=403, detail="Only admins can view other user profiles"
        )

    user = await user_service.get_user_with_details(user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ✅ SEARCH USERS (ADMIN)
@user_router.get("/search", response_model=UserSearchResponse)
async def search_users(
    query: str | None = None,
    skip: int = 0,
    limit: int = 10,
    current_user: JwtPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Search users by phone number, name, or email (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can search users")

    results = await user_service.search_users(
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
    user_service: UserService = Depends(get_user_service),
):
    """Get all users with pagination (admin only)"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view all users")

    users = await user_service.get_all_users(skip=skip, limit=limit)

    return UserListResponse(users=users, total=len(users), skip=skip, limit=limit)
