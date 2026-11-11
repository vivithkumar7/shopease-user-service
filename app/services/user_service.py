from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_model import UserProfile
from app.schemas.user_schema import ProfileCreate, ProfilePatch, ProfileUpdate


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A profile already exists for this authenticated user",
        ) from None


def get_profile(db: Session, auth_user_id: int) -> UserProfile:
    profile = db.scalar(
        select(UserProfile).where(UserProfile.auth_user_id == auth_user_id)
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    if not profile.is_active:
        raise HTTPException(status_code=403, detail="User profile is deactivated")
    return profile


def create_profile(
    db: Session, auth_user_id: int, data: ProfileCreate
) -> UserProfile:
    profile = UserProfile(auth_user_id=auth_user_id, **data.model_dump())
    db.add(profile)
    _commit(db)
    db.refresh(profile)
    return profile


def update_profile(
    db: Session, auth_user_id: int, data: ProfileUpdate | ProfilePatch
) -> UserProfile:
    profile = get_profile(db, auth_user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    _commit(db)
    db.refresh(profile)
    return profile


def deactivate_profile(db: Session, auth_user_id: int) -> UserProfile:
    profile = db.scalar(
        select(UserProfile)
        .where(UserProfile.auth_user_id == auth_user_id)
        .with_for_update()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    if profile.is_active:
        profile.is_active = False
        _commit(db)
        db.refresh(profile)
    return profile


def delete_profile(db: Session, auth_user_id: int) -> None:
    profile = get_profile(db, auth_user_id)
    db.delete(profile)
    db.commit()