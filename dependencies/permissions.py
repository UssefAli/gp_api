from fastapi import Depends, HTTPException
from core.auth import current_active_user
from app.db.models import User
import uuid

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

# def admin_or_owner(user_id_param: str = "user_id"):
#     async def checker(
#         user_id: uuid.UUID,
#         current_user: User = Depends(current_active_user),
#     ):
#         if current_user.is_superuser:
#             return current_user

#         if current_user.id != user_id:
#             raise HTTPException(
#                 status_code=403,
#                 detail="Not enough permissions",
#             )

#         return current_user

#     return checker

