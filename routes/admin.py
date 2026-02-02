from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.schemas import MechanicAdminUpdate, SkillCreate, UserUpdate
from dependencies.helper import Status, swagger_responses
from dependencies.permissions import require_admin
from db.models import Rating, Skill, get_async_session , User , ServiceRequest 
import uuid

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)



@router.get(
    "/skills",
    status_code=200,
    summary="Get all skills",
    description="Retrieve the list of all available skills. Admin access required.",
    responses=swagger_responses(
        success_message={
            "skills": [
                {"skill id": 1, "skill name": "engine"},
                {"skill id": 2, "skill name": "tires"}
            ]
        },
        access_role="Admin"
    ),
)
async def get_all_skills(
    session: AsyncSession = Depends(get_async_session),
    admin=Depends(require_admin),
):
    try:
        result = await session.execute(select(Skill))
        skills = result.scalars().all()
        skills_list = [{"skill id": skill.skill_id, "skill name": skill.skill_name} for skill in skills]
        return {"skills": skills_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@router.get(
    "/ratings",
    status_code=200,
    summary="Get all ratings",
    description="""
Retrieve all ratings in the system.

🛡 **Admin access required**

Includes:
- User & mechanic IDs
- Rating value
- Feedback
- Creation date
    """,
    responses=swagger_responses(
        success_message={
            "ratings": [
                {
                    "id": 1,
                    "request id": 45,
                    "user id": "uuid",
                    "mechanic id": "uuid",
                    "rate": 5,
                    "feedback": "Excellent service",
                    "created at": "2024-01-10T12:30:00"
                }
            ]
        },
        access_role="Admin",
    ),
)
async def get_all_ratings(
    session: AsyncSession = Depends(get_async_session),
    admin=Depends(require_admin),
):
    try:
        result = await session.execute(select(Rating).order_by(Rating.created_at.desc()))
        ratings = result.scalars().all()
        rating_list = []

        for rating in ratings:
            rating_list.append({
                "id": rating.rating_id,
                "request id": rating.request_id,
                "user id": rating.user_id,
                "mechanic id": rating.mechanic_id,
                "rate": rating.rating,
                "feedback": rating.feedback_text,
                "created at": rating.created_at
            })
        return {"ratings": rating_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@router.post(
    "/skills/add",
    status_code=201,
    summary="Add a new skill",
    description="Add a new skill to the system. Admin access required.",
    responses=swagger_responses(
        success_message={"skill": {"skill id": 3, "skill name": "brakes"}},
        access_role="Admin"
    ),
)
async def add_skill(
    skill: SkillCreate,
    session: AsyncSession = Depends(get_async_session),
    admin=Depends(require_admin),
):
    try:
        new_skill = Skill(skill_name=skill.skill_name)
        session.add(new_skill)
        await session.commit()
        await session.refresh(new_skill)
        return {"skill": {"skill id": new_skill.skill_id, "skill name": new_skill.skill_name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.delete(
    "/request/{request_id}",
    status_code=200,
    summary="Delete a service request",
    description="Delete a specific service request by ID. Admin access required.",
    responses=swagger_responses(
        success_message={"message": "Request deleted successfully"},
        access_role="Admin"
    ),
)
async def delete_request(
    request_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin=Depends(require_admin),
):
    try:
        result = await session.execute(select(ServiceRequest).where(ServiceRequest.request_id == request_id))
        request = result.scalar_one_or_none()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        await session.delete(request)
        await session.commit()
        return {"message": "Request deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.delete(
    "/account/{id}",
    status_code=200,
    summary="Delete a user account",
    description="Delete a specific user account by ID. Admin access required.",
    responses=swagger_responses(
        success_message={"message": "Account deleted successfully"},
        access_role="Admin"
    ),
)
async def delete_account(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    admin=Depends(require_admin),
):
    try:
        result = await session.execute(select(User).where(User.id == id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await session.delete(user)
        await session.commit()
        return {"message": "Account deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.delete(
    "/rating/{rating_id}",
    status_code=200,
    summary="Delete a rating",
    description="Delete a specific rating and update the mechanic's average rating. Admin access required.",
    responses=swagger_responses(
        success_message={"message": "Rating deleted successfully"},
        access_role="Admin"
    ),
)
async def delete_rating(
    rating_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin=Depends(require_admin),
):
    try:
        result = await session.execute(select(Rating).where(Rating.rating_id == rating_id))
        rating = result.scalar_one_or_none()
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found")

        mechanic_id = rating.mechanic_id
        await session.delete(rating)
        await session.commit()

        # Recalculate mechanic avg rating
        result1 = await session.execute(select(User).where(User.id == mechanic_id))
        mechanic = result1.scalar_one_or_none()
        if not mechanic:
            raise HTTPException(status_code=404, detail="Mechanic not found")

        result2 = await session.execute(select(Rating).where(Rating.mechanic_id == mechanic_id))
        ratings = result2.scalars().all()
        if ratings:
            mechanic.avg_rating = sum(r.rating for r in ratings) / len(ratings)
        else:
            mechanic.avg_rating = 0
        mechanic.review_count = len(ratings)

        await session.commit()
        await session.refresh(mechanic)

        return {"message": "Rating deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.delete(
    "/skills/{skill_id}",
    status_code=200,
    summary="Delete a skill",
    description="Delete a specific skill by ID. Admin access required.",
    responses=swagger_responses(
        success_message={"message": "Skill deleted successfully"},
        access_role="Admin"
    ),
)
async def delete_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin=Depends(require_admin),
):
    try:
        result = await session.execute(select(Skill).where(Skill.skill_id == skill_id))
        skill = result.scalar_one_or_none()
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        await session.delete(skill)
        await session.commit()
        return {"message": "Skill deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.get(
    "/request/{request_id}",
    status_code=200,
    summary="Get specific request",
    description="Retrieve a specific service request by ID along with user and mechanic details. Admin access required.",
    responses=swagger_responses(
        success_message={
            "request": {
                "request id": 42,
                "user id": "uuid",
                "user name": "Mohamed Ali",
                "mechanic id": "uuid",
                "mechanic name": "Ahmed Khalid",
                "status": "Completed",
                "type": "engine",
                "created at": "2024-01-05T14:30:00",
                "completed_at": "2024-01-05T15:45:00"
            }
        },
        access_role="Admin"
    ),
)
async def get_specific_request(
    request_id: int,
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await session.execute(select(ServiceRequest).where(ServiceRequest.request_id == request_id))
        request = result.scalar_one_or_none()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        result1 = await session.execute(select(User).where(User.id == request.user_id))
        user = result1.scalar_one_or_none()

        result2 = await session.execute(select(User).where(User.id == request.mechanic_id))
        mechanic = result2.scalar_one_or_none()

        mechanic_id = mechanic.id if mechanic else "----"
        mechanic_name = mechanic.name if mechanic else "----"
        completed_at = request.completed_at if request.status == Status.completed else "----"

        request_details = {
            "request id": request.request_id,
            "user id": request.user_id,
            "user name": user.name,
            "mechanic id": mechanic_id,
            "mechanic name": mechanic_name,
            "status": request.status,
            "type": request.request_type,
            "created at": request.created_at,
            "completed_at": completed_at,
        }

        return {"request": request_details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.get(
    "/users",
    status_code=200,
    summary="Get all users",
    description="""
Retrieve all users in the system.

🔒 **Authentication required**  
🛡 **Admin access required**
    """,
    responses=swagger_responses(access_role="admin" , success_message={"users":[
                    {
                    "id": "8d9f0e3e-9c2e-4d12-bf3a-9e7e1eacb123",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+123456789",
                    "car model": "Toyota Corolla",
                    "car type": "Sedan",
                    "Canceled count" : 2
                }
            ]
        },
    )
)
async def get_all_users(session : AsyncSession = Depends(get_async_session) , admin = Depends(require_admin)):
    try:
        result = await session.execute(select(User).where(User.role == "user").order_by(User.created_at.desc()))
        users = result.scalars().all()
        users_list = []
        for user in users:
            users_list.append(
            {
                "id" : user.id,
                "name" : user.name,
                "email" : user.email,
                "phone" : user.phone,
                "car model" : user.car_model,
                "car type" : user.car_type,
                "Canceled count" : user.canceled_count
            }     
            )
        return {"users" : users_list}
    except Exception as e:
        raise HTTPException(status_code=500 , detail = str(e))






@router.get(
    "/user/{id}",
    status_code=200,
    summary="Get specific user by ID",
    description="""
Retrieve a specific user by their ID.

🔒 **Authentication required**  
🛡 **Admin access required**
    """,
    responses=swagger_responses(
        access_role="Admin",
        success_message={"user" : 
                    {
                    "id": "8d9f0e3e-9c2e-4d12-bf3a-9e7e1eacb123",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+123456789",
                    "car model": "Toyota Corolla",
                    "car type": "Sedan",
                    "Canceled count" : 2
                }
        },
        bad_request_message="this is a mechanic id",
        not_found=True,
        validation=True
    )
)
async def get_specific_user(id : uuid.UUID ,session : AsyncSession = Depends(get_async_session) , admin = Depends(require_admin)):

    try:
        result = await session.execute(select(User).where(User.id == id))  
        u_user = result.scalar_one_or_none()
        if not u_user:
            raise HTTPException(status_code=404 , detail = "User not found")
        if u_user.role == "mechanic":
            raise HTTPException(status_code=400 , detail="this is a mechanic id")
        cur_user = {
                "name" : u_user.name,
                "email" : u_user.email,
                "phone" : u_user.phone,
                "car model" : u_user.car_model,
                "car type" : u_user.car_type,
                "Canceled count" : u_user.canceled_count
        }     
        return {"user" : cur_user}
    except Exception as e:
        raise HTTPException(status_code=500 , detail= str(e))






@router.patch(
    "/user/{id}",
    status_code=200,
    summary="Update specific user by ID",
    description="""
Update a specific user's profile.

🔒 **Authentication required**  
🛡 **Admin access required**

✏️ **Partial update supported**
    """,
    responses=swagger_responses(
        access_role="Admin",
        success_message={"message":"User profile updated successfully"},
        bad_request_message="this is a mechanic id",
        not_found=True,
        validation=True

    )
)
async def update_specific_user( user_in: UserUpdate , id : uuid.UUID ,session : AsyncSession = Depends(get_async_session) , admin = Depends(require_admin)):
    
    try:
        result = await session.execute(
            select(User).where(User.id == id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.role == "mechanic":
            raise HTTPException(status_code=400 , detail="this is a mechanic id")

        if user_in.name != "":
            user.name = user_in.name
        if user_in.email != "":
            user.email = user_in.email
        if user_in.phone != "":
            user.phone = user_in.phone
        if user_in.car_type != "":
            user.car_type = user_in.car_type
        if user_in.car_model != "":
            user.car_model = user_in.car_model
        if user_in.car_model != "":
            user.car_model = user_in.car_model

        await session.commit()
        await session.refresh(user)

        return {"messgae" : "User profile updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.get(
    "/mechanics",
    status_code=200,
    summary="Get all mechanics",
    description="""
Retrieve a list of all mechanics in the system.

Each mechanic includes:
- Personal contact information
- Workshop details and location
- Availability status
- Performance statistics

🔒 Authentication required  
🛡 Admin access required
    """,
    responses=swagger_responses(
        success_message={
            "mechanics" : [
                {
                "id": "7c2f1b9a-4f6d-4e88-9a21-91a3f9e8c456",
                "name": "Ahmed Hassan",
                "email": "ahmed.hassan@autofix.com",
                "phone": "+201012345678",
                "workshop name": "AutoFix Garage",
                "workshop lat": 30.0444,
                "workshop lng": 31.2357,
                "rating": 4.7,
                "experince years": 8,
                "total jops": 312,
                "available": True,
                "review count": 128,
                "Canceled count": 6
            }
            ]
        },
        access_role="Admin",
    ),
)
async def get_all_mechanics(session : AsyncSession = Depends(get_async_session) , admin = Depends(require_admin)):
    
    try:
        result = await session.execute(select(User).where(User.role == "mechanic").order_by(User.created_at.desc()))
        mechanics = result.scalars().all()   
        mechanics_list = []
        for mechanic in mechanics:
            mechanics_list.append(
            {
                "id" : mechanic.id,
                "name" : mechanic.name,
                "email" : mechanic.email,
                "phone" : mechanic.phone,
                "workshop name" : mechanic.workshop_name,
                "workshop lat" : mechanic.workshop_lat,
                "workshop lng" : mechanic.workshop_lng,
                "rating" : mechanic.avg_rating,
                "experince years" : mechanic.experience_years,
                "total jops" : mechanic.total_jobs,
                "available" : mechanic.is_available,
                "review count" : mechanic.review_count,
                "Canceled count" : mechanic.canceled_count
            }     
            )
        return {"mechanics" : mechanics_list}
    except Exception as e:
        raise HTTPException(status_code=500 , detail=str(e))






@router.get(
    "/mechanic/{id}",
    status_code=200,
    summary="Get mechanic by ID",
    description="""
Retrieve a specific mechanic profile by ID.

Returns full mechanic information including:
- Workshop details and location
- Availability status
- Ratings and job statistics

📌 If the ID belongs to a normal user, the request will fail.

🔒 Authentication required  
🛡 Admin access required
    """,
    responses=swagger_responses(
        success_message={
            "mechanic" : {
                "id": "7c2f1b9a-4f6d-4e88-9a21-91a3f9e8c456",
                "name": "Ahmed Hassan",
                "email": "ahmed.hassan@autofix.com",
                "phone": "+201012345678",
                "workshop name": "AutoFix Garage",
                "workshop lat": 30.0444,
                "workshop lng": 31.2357,
                "rating": 4.7,
                "experince years": 8,
                "total jops": 312,
                "available": True,
                "review count": 128,
                "Canceled count": 6
            }
        },
        not_found=True,
        bad_request_message="this is a user id not a mechanic",
        validation=True,
        access_role="Admin"
    ),
)
async def get_specific_mechanic(id : uuid.UUID,session : AsyncSession = Depends(get_async_session) , admin = Depends(require_admin)):

    result = await session.execute(select(User).where(User.id == id))  
    mechanic = result.scalar_one_or_none()
    
    if not mechanic:
        raise HTTPException(status_code=404 , detail= "User not found")
    if mechanic.role == "user":
        raise HTTPException(status_code=400 , detail= "this is a user id not a mechanic")
    
    current_mechanic = {
        "id" : mechanic.id,
        "name" : mechanic.name,
        "email" : mechanic.email,
        "phone" : mechanic.phone,
        "workshop name" : mechanic.workshop_name,
        "rating" : mechanic.avg_rating,
        "experince years" : mechanic.experience_years,
        "total jops" : mechanic.total_jobs,
        "review count" : mechanic.review_count,
        "available" : mechanic.is_available,
        "Canceled count" : mechanic.canceled_count
    }

    return {"mechanic" : current_mechanic}






@router.patch(
    "/mechanic/{id}",
    status_code=200,
    summary="Update mechanic by ID",
    description="""
Update a mechanic profile by ID.

✏️ Partial update supported  
Admin can update:
- Personal information
- Workshop details
- Ratings and statistics
- Job and review counters

🔒 Authentication required  
🛡 Admin access required
    """,
    responses=swagger_responses(
        success_message="Mechanic profile updated successfully",
        bad_request_message="this is a user id not a mechanic",
        not_found=True,
        validation=True,
        access_role="Admin"
    ),
)
async def update_specific_mechanic(id : uuid.UUID,user_in : MechanicAdminUpdate , session : AsyncSession = Depends(get_async_session) , admin = Depends(require_admin)):
    try:
        result = await session.execute(
            select(User).where(User.id == id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.role == "user":
            raise HTTPException(status_code=400, detail="this is a user id not a mechanic")

        if user_in.name != "":
            user.name = user_in.name
        if user_in.email != "":
            user.email = user_in.email
        if user_in.phone != "":
            user.phone = user_in.phone
        if user_in.workshop_name != "":
            user.workshop_name = user_in.workshop_name       
        if user_in.experience_years != -1:
            user.experience_years = user_in.experience_years
        if user_in.avg_rating != -1:
            user.avg_rating = user_in.avg_rating
        if user_in.review_count != -1:
            user.review_count = user_in.review_count
        if user_in.total_jobs != -1:
            user.total_jobs = user_in.total_jobs
        if user_in.canceled_count != -1:
            user.canceled_count = user_in.canceled_count
      

        await session.commit()
        await session.refresh(user)
        return {"messgae" : "mechanic profile updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@router.patch("/admin/promote/{user_id}")
async def promote_to_admin(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    admin=Depends(require_admin),
):
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_superuser = True
    user.is_verified = True

    await session.commit()
    return {"message": "User promoted to admin"}