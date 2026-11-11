from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.security import CurrentAuthUserId
from app.database.connection import get_db
from app.schemas.user_schema import ProfileCreate, ProfilePatch, ProfileRead, ProfileUpdate
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/profile",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    data: ProfileCreate,
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> ProfileRead:
    return user_service.create_profile(db, auth_user_id, data)


@router.get("/profile", response_model=ProfileRead)
def read_profile(
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> ProfileRead:
    return user_service.get_profile(db, auth_user_id)


@router.put("/profile", response_model=ProfileRead)
def replace_profile(
    data: ProfileUpdate,
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> ProfileRead:
    return user_service.update_profile(db, auth_user_id, data)


@router.patch("/profile", response_model=ProfileRead)
def patch_profile(
    data: ProfilePatch,
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> ProfileRead:
    return user_service.update_profile(db, auth_user_id, data)


@router.post("/profile/deactivate", response_model=ProfileRead)
def deactivate_profile(
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> ProfileRead:
    return user_service.deactivate_profile(db, auth_user_id)


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> Response:
    user_service.delete_profile(db, auth_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)