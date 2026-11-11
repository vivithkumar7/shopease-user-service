from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.security import CurrentAuthUserId
from app.database.connection import get_db
from app.schemas.address_schema import AddressCreate, AddressRead, AddressUpdate
from app.services import address_service

router = APIRouter(prefix="/api/users/addresses", tags=["addresses"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    data: AddressCreate,
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> AddressRead:
    return address_service.create_address(db, auth_user_id, data)


@router.get("", response_model=list[AddressRead])
def list_addresses(
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> list[AddressRead]:
    return address_service.list_addresses(db, auth_user_id)


@router.get("/{address_id}", response_model=AddressRead)
def read_address(
    address_id: int,
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> AddressRead:
    return address_service.get_address(db, auth_user_id, address_id)


@router.put("/{address_id}", response_model=AddressRead)
def replace_address(
    address_id: int,
    data: AddressUpdate,
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> AddressRead:
    return address_service.update_address(db, auth_user_id, address_id, data)


@router.patch("/{address_id}/default", response_model=AddressRead)
def make_default_address(
    address_id: int,
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> AddressRead:
    return address_service.set_default_address(db, auth_user_id, address_id)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_address(
    address_id: int,
    auth_user_id: CurrentAuthUserId,
    db: DbSession,
) -> Response:
    address_service.delete_address(db, auth_user_id, address_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)