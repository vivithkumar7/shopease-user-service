from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.address_model import UserAddress
from app.models.user_model import UserProfile
from app.schemas.address_schema import AddressCreate, AddressUpdate


def _lock_active_profile(db: Session, auth_user_id: int) -> UserProfile:
    profile = db.scalar(
        select(UserProfile)
        .where(UserProfile.auth_user_id == auth_user_id)
        .with_for_update()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    if not profile.is_active:
        raise HTTPException(status_code=403, detail="User profile is deactivated")
    return profile


def _owned_address(
    db: Session, profile: UserProfile, address_id: int
) -> UserAddress:
    address = db.get(UserAddress, address_id)
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    if address.user_id != profile.id:
        raise HTTPException(status_code=403, detail="Address access is forbidden")
    return address


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Address could not be saved because it conflicts with existing data",
        ) from None


def create_address(
    db: Session, auth_user_id: int, data: AddressCreate
) -> UserAddress:
    profile = _lock_active_profile(db, auth_user_id)
    values = data.model_dump()
    if values["is_default"]:
        db.execute(
            update(UserAddress)
            .where(UserAddress.user_id == profile.id)
            .values(is_default=False)
        )
    address = UserAddress(user_id=profile.id, **values)
    db.add(address)
    _commit(db)
    db.refresh(address)
    return address


def list_addresses(db: Session, auth_user_id: int) -> list[UserAddress]:
    profile = _lock_active_profile(db, auth_user_id)
    return list(
        db.scalars(
            select(UserAddress)
            .where(UserAddress.user_id == profile.id)
            .order_by(UserAddress.id)
        ).all()
    )


def get_address(
    db: Session, auth_user_id: int, address_id: int
) -> UserAddress:
    profile = _lock_active_profile(db, auth_user_id)
    return _owned_address(db, profile, address_id)


def update_address(
    db: Session,
    auth_user_id: int,
    address_id: int,
    data: AddressUpdate,
) -> UserAddress:
    profile = _lock_active_profile(db, auth_user_id)
    address = _owned_address(db, profile, address_id)
    values = data.model_dump()
    if values["is_default"]:
        db.execute(
            update(UserAddress)
            .where(
                UserAddress.user_id == profile.id,
                UserAddress.id != address.id,
            )
            .values(is_default=False)
        )
    for field, value in values.items():
        setattr(address, field, value)
    _commit(db)
    db.refresh(address)
    return address


def set_default_address(
    db: Session, auth_user_id: int, address_id: int
) -> UserAddress:
    profile = _lock_active_profile(db, auth_user_id)
    address = _owned_address(db, profile, address_id)
    db.execute(
        update(UserAddress)
        .where(
            UserAddress.user_id == profile.id,
            UserAddress.id != address.id,
        )
        .values(is_default=False)
    )
    address.is_default = True
    _commit(db)
    db.refresh(address)
    return address


def delete_address(db: Session, auth_user_id: int, address_id: int) -> None:
    profile = _lock_active_profile(db, auth_user_id)
    address = _owned_address(db, profile, address_id)
    db.delete(address)
    db.commit()