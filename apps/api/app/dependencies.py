from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Stub: Extract and verify Clerk token, lookup internal user record."""
    # TODO: Implement Clerk token verification
    # 1. Extract Bearer token from Authorization header
    # 2. Verify with Clerk SDK
    # 3. Lookup user in users/sub_users/owner_users based on metadata.user_type
    # 4. Return user context dict
    return None
