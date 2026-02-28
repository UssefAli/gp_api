import uuid
from fastapi import FastAPI 
from app.db.schemas import AdminCreate, AdminRead, MechanicCreate, MechanicRead, UserCreate , UserRead 
from app.db.models import User, create_db_and_tables 
from contextlib import asynccontextmanager
from core.auth import auth_backend , fastapi_users, get_user_manager
from routes import admin , mechanics, tracking, users , requests , ratings
from fastapi.middleware.cors import CORSMiddleware

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_users import BaseUserManager, FastAPIUsers
import resend


app = FastAPI()


app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth/user",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(AdminRead, AdminCreate),
    prefix="/auth/admin",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(MechanicRead, MechanicCreate),
    prefix="/auth/mechanic",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth/user",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_verify_router(MechanicRead),
    prefix="/auth/Mechanic",
    tags=["auth"],
)

app.include_router(users.router)
app.include_router(mechanics.router)
app.include_router(requests.router)
app.include_router(tracking.router)
app.include_router(ratings.router)
app.include_router(admin.router)