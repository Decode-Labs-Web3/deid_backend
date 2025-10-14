"""
Router for syncing profile to blockchain via DEiDProfile through proxy.
"""

from fastapi import APIRouter, Depends
from app.api.deps.decode_guard import AuthenticatedUser, get_current_user
from app.api.services.sync_profile_service import SyncProfileService

router = APIRouter(prefix="", tags=["Sync Profile"])


@router.post("/create-profile")
async def create_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Prepare calldata for createProfile. Returns calldata and metadataURI; frontend submits via wallet.
    """
    print(f"Creating profile for user: {current_user.user_id}")
    service = SyncProfileService()
    result = await service.create_profile_prepare(current_user.user_id)
    return {
        "success": True,
        "statusCode": 200,
        "message": "Calldata prepared",
        "data": result,
    }

@router.post("/update-profile")
async def update_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Prepare calldata for updateProfile. Returns calldata and metadataURI; frontend submits via wallet.
    """
    print(f"Updating profile for user: {current_user.user_id}")
    service = SyncProfileService()
    result = await service.update_profile_prepare(current_user.user_id)
    return {
        "success": True,
        "statusCode": 200,
        "message": "Update calldata prepared",
        "data": result,
    }
