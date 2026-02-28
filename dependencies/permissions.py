from fastapi import Depends, HTTPException, WebSocket, WebSocketException , status
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from core.auth import UserManager, current_active_user, get_jwt_strategy , fastapi_users, get_user_manager
from app.db.models import User, get_async_session
import uuid
from sqlalchemy.ext.asyncio import AsyncSession




async def require_user_ws(
    websocket: WebSocket,
    session: AsyncSession = Depends(get_async_session),
) -> User:

    auth_header = websocket.headers.get("authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Missing or invalid authorization header",
        )

    token = auth_header.split(" ")[1]

    jwt_strategy = get_jwt_strategy()

    try:
        payload = await jwt_strategy.read_token(token)
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired token",
        )

    user_db = SQLAlchemyUserDatabase(session, User)
    user_manager = UserManager(user_db)

    user = await user_manager.get(user_id)

    if not user or not user.is_active:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Unauthorized",
        )

    return user





async def require_user(user: User = Depends(current_active_user)):
    if user.role != "user":
        raise HTTPException(status_code=403, detail="User access required")
    return user




async def require_mechanic(user: User = Depends(current_active_user)):
    if user.role != "mechanic":
        raise HTTPException(status_code=403, detail="Mechanic access required")
    return user





async def require_admin(user: User = Depends(current_active_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")  
    return user





async def require_mechanic_or_user(user: User = Depends(current_active_user)):
    if user.role not in ("mechanic" , "user"):
        raise HTTPException(status_code=403, detail="Access required")
    return user


