from fastapi import HTTPException, Depends , APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.helper import swagger_responses
from dependencies.permissions import require_admin, require_mechanic_or_user,require_user
from app.db.schemas import RatingCreate, UserUpdate 
from app.db.models import Rating, get_async_session , User 
import uuid




router = APIRouter(
    prefix="/users",
    tags=["user"]
)


@router.get(
    "/account",
    status_code=200,
    summary="Get current logged account profile",
    description="""
Retrieve the profile of the authenticated account.

🔒 **Authentication required**
    """,
    responses=swagger_responses(
        success_message={
            "user":{                 
                    "id": "8d9f0e3e-9c2e-4d12-bf3a-9e7e1eacb123",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+123456789",
                    "car model": "Toyota Corolla",
                    "car type": "Sedan",
                    "workshop name": "AutoFix Garage",
                    "rating": 4.7,
                    "experince years": 8,
                    "total jops": 312,
                    "available": True,
                    "review count": 128,
                    "Canceled count" : 2,
                    "active" : True,
                    "verified" : True,
                    "superuser" : False
            }
        },
        access_role=""
    )
)
async def get_current_account_details(session : AsyncSession = Depends(get_async_session) , cur_user : User = Depends(require_mechanic_or_user)):
    try:

        user = {
                "id" : cur_user.id,
                "name" : cur_user.name,
                "email" : cur_user.email,
                "phone" : cur_user.phone,
                "role" : cur_user.role,
                "car model" : cur_user.car_model if cur_user.role == 'user' else "",
                "car type" : cur_user.car_type if cur_user.role == 'user' else "",
                "workshop name" : cur_user.workshop_name if cur_user.role == 'mechanic' else "",
                "rating" : cur_user.avg_rating if cur_user.role == 'mechanic' else "",
                "experince years" : cur_user.experience_years if cur_user.role == 'mechanic' else "",
                "total jops" : cur_user.total_jobs if cur_user.role == 'mechanic' else "",
                "available" : cur_user.is_available if cur_user.role == 'mechanic' else "",
                "review count" : cur_user.review_count if cur_user.role == 'mechanic' else "",
                "Canceled count" : cur_user.canceled_count if cur_user.role == 'mechanic' else "",
                "active" : cur_user.is_active,
                "verified" : cur_user.is_verified,
                "superuser" : cur_user.is_superuser

        }     
        return {"user" : user}
    except Exception as e:
        raise HTTPException(status_code=500 , detail = str(e))



@router.get(
    "/me",
    status_code=200,
    summary="Get current user profile",
    description="""
Retrieve the profile of the authenticated user.

🔒 **Authentication required**
    """,
    responses=swagger_responses(
        success_message={
            "user":{                 
                    "id": "8d9f0e3e-9c2e-4d12-bf3a-9e7e1eacb123",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+123456789",
                    "car model": "Toyota Corolla",
                    "car type": "Sedan",
                    "Canceled count" : 2
            }
        },
        access_role="User"
    )
)
async def get_current_user(session : AsyncSession = Depends(get_async_session) , cur_user : User = Depends(require_user)):
    try:
        user = {
                "id" : cur_user.id,
                "name" : cur_user.name,
                "email" : cur_user.email,
                "phone" : cur_user.phone,
                "car model" : cur_user.car_model,
                "car type" : cur_user.car_type,
                "Canceled count" : cur_user.canceled_count
        }     
        return {"user" : user}
    except Exception as e:
        raise HTTPException(status_code=500 , detail = str(e))






@router.patch(
    "/me",
    status_code=200,
    summary="Update current user profile",
    description="""
    Update the authenticated user's profile.

🔒 **Authentication required**  
Only logged-in users can access this endpoint.

✏️ **Partial update supported**  
Send only the fields you want to update.
    """,
    responses=swagger_responses(
        success_message={"message":"User profile updated successfully"},
        access_role="User",
        validation=True
    )
)
async def update_current_user( user_in: UserUpdate ,session : AsyncSession = Depends(get_async_session) , cur_user : User = Depends(require_user)):    
    try:      
        if user_in.name != "":
            cur_user.name = user_in.name
        if user_in.email != "":
            cur_user.email = user_in.email
        if user_in.phone != "":
            cur_user.phone = user_in.phone
        if user_in.car_type != "":
            cur_user.car_type = user_in.car_type
        if user_in.car_model != "":
            cur_user.car_model = user_in.car_model

        await session.commit()
        await session.refresh(cur_user)

        return {"messgae" : "User profile updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500,  detail=str(e))






@router.patch(
    "/location/me",
    status_code=200,
    summary="Update current user location",
    description="""
Update the authenticated user's location.

🔒 **Authentication required**
    """,
    responses=swagger_responses(
        access_role="User",
        success_message={"message":"Location updated successfully"},
        validation=True
    )
)
async def update_user_location(
    lat : float,
    lng : float,
    session : AsyncSession = Depends(get_async_session),
    cur_user : User = Depends(require_user),
):
    try:
        result = await session.execute(select(User).where(User.id == cur_user.id))
        user = result.scalar_one_or_none()
        user.user_lat = lat
        user.user_lng = lng
        
        await session.commit()
        await session.refresh(user)
        return {"message" : "Location updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500 , detail=str(e))



