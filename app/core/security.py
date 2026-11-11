from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_auth_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
) -> int:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require_exp": True},
        )
        auth_user_id = payload.get(settings.JWT_USER_ID_CLAIM)
        if isinstance(auth_user_id, bool) or not isinstance(auth_user_id, (int, str)):
            raise ValueError("User ID claim must be an integer")
        if isinstance(auth_user_id, str) and (
            not auth_user_id.isascii() or not auth_user_id.isdecimal()
        ):
            raise ValueError("User ID claim must be an integer")
        parsed_user_id = int(auth_user_id)
        if parsed_user_id <= 0:
            raise ValueError("User ID claim must be positive")
    except (JWTError, TypeError, ValueError):
        raise unauthorized from None

    return parsed_user_id


CurrentAuthUserId = Annotated[int, Depends(get_current_auth_user_id)]