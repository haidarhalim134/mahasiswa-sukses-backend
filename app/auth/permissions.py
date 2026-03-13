from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import Visibility
from app.core.supabase import supabase
from app.db.session import get_db
from app.core.config import settings
from app.users.service import get_user_by_id
from app.users.models import Role


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def verify_supabase_token(token: str):

    try:
        payload = supabase.auth.get_claims(token)

        assert payload != None

        user_id: str = payload['claims']['sub']

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token",
            )

        return user_id

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

# TODO: separate authentication and authorization
def require_user(
    role: Optional[Role] = None,
    roles: Optional[List[Role]] = None,
    visibility: Visibility = Visibility.public,
):

    async def dependency(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
        user_id: Optional[str] = None,
    ):

        user_id_from_token = await verify_supabase_token(token)

        current_user = await get_user_by_id(db, UUID(user_id_from_token))

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if current_user.role == Role.admin:
            return current_user


        if role and current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )

        if roles and current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )

        if visibility == Visibility.private:
            if user_id and user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot access other users",
                )

        return current_user

    return dependency