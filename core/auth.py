import uuid
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from app.db.models import User, get_user_db
from services.email import CustomEmailManager
from dotenv import load_dotenv
import os

load_dotenv()

SECRET = os.getenv("SECRET")

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET
    reset_password_token_secret: str = SECRET
    reset_password_token_lifetime_seconds: int = 3600


    def __init__(self, user_db):
        super().__init__(user_db)
        self.email_manager = CustomEmailManager()
        
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        token = await self.request_verify(user, request)
        print(f"Verification token for {user.email}: {token}")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):

        success = await self.email_manager.send_password_reset(user, token, self)
        
        if success:
            print(f"✅ Password reset email sent to {user.email}")
        else:
            print(f"❌ Failed to send email")

        print(f"\n🔑 DEBUG Token: {token}")   
     
    async def on_after_reset_password(
        self, 
        user: User, 
        request: Optional[Request] = None
    ) -> None:
        
        print(f"🔄 Password reset successful for {user.email}")


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")


def get_jwt_strategy():
    return JWTStrategy(secret=SECRET, lifetime_seconds=172800)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
