from datetime import datetime, timezone
from decimal import Decimal
from typing import Set
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.helper import SkillName, Status, swagger_responses
from dependencies.permissions import require_admin, require_mechanic
from app.db.schemas import MechanicAdminUpdate, MechanicRead, MechanicSkillCreate, MechanicUpdate
from app.db.models import LocationTracking, MechanicSkill, ServiceRequest, Skill, get_async_session , User 
import uuid
from services.webscoket_manager import manager
from services.distance import haversine_distance




router = APIRouter(
    prefix="/mechanics",
    tags=["mechanic"]
)






@router.get(
    "/me",
    status_code=200,
    summary="Get current mechanic profile",
    description="""
Retrieve the profile of the authenticated mechanic.

Returns mechanic information such as:
- Contact details
- Workshop name
- Rating and experience
- Job and review count

🔒 Mechanic authentication required
    """,
    responses=swagger_responses(
        success_message={"mechanic" : {
                "id": "7c2f1b9a-4f6d-4e88-9a21-91a3f9e8c456",
                "name": "Ahmed Hassan",
                "email": "ahmed.hassan@autofix.com",
                "phone": "+201012345678",
                "workshop name": "AutoFix Garage",
                "rating": 4.7,
                "experince years": 8,
                "total jops": 312,
                "available": True,
                "review count": 128,
        }},
        access_role="Mechanic"
    ),
)
async def get_current_mechanic(session : AsyncSession = Depends(get_async_session) , mechanic = Depends(require_mechanic)):

    try:
        result = await session.execute(select(User).where(User.id == mechanic.id))
        mechanic = result.scalar_one_or_none()
        current_mechanic = {
            "id" : mechanic.id,
            "name" : mechanic.name,
            "email" : mechanic.email,
            "phone" : mechanic.phone,
            "workshop name" : mechanic.workshop_name,
            "rating" : mechanic.avg_rating,
            "experince years" : mechanic.experience_years,
            "total jops" : mechanic.total_jobs,
            "available" : mechanic.is_available,
            "review count" : mechanic.review_count
        }
        return {"mechanic" : current_mechanic}
    except Exception as e:
        raise HTTPException(status_code=500 , detail=str(e))






@router.patch(
    "/me",
    status_code=200,
    summary="Update current mechanic profile",
    description="""
Update the authenticated mechanic profile.

✏️ Partial update supported  
Only provided fields will be updated.

Fields include:
- Name
- Email
- Phone
- Workshop name
- Experience years

🔒 Mechanic authentication required
    """,
    responses=swagger_responses(
        success_message={"message":"Mechanic profile updated successfully"},
        validation=True,
        access_role="Mechanic",
    ),
)
async def update_current_mechanic(user_in : MechanicUpdate , session : AsyncSession = Depends(get_async_session) , cur_mechanic = Depends(require_mechanic)):
    try:
        if user_in.name != "":
            cur_mechanic.name = user_in.name
        if user_in.email != "":
            cur_mechanic.email = user_in.email
        if user_in.phone != "":
            cur_mechanic.phone = user_in.phone
        if user_in.workshop_name != "":
            cur_mechanic.workshop_name = user_in.workshop_name       
        if user_in.experience_years != -1:
            cur_mechanic.experience_years = user_in.experience_years

        await session.commit()
        await session.refresh(cur_mechanic)
        return {"messgae" : "Mechanic profile updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.patch(
    "/workshop_location/me",
    status_code=200,
    summary="Set/Update mechanic workshop location",
    description="""
Update the workshop location of the authenticated mechanic.

Updates:
- Workshop latitude
- Workshop longitude

Used for nearby job matching.

🔒 Mechanic authentication required
    """,
    responses=swagger_responses(
        success_message={"message":"Location updated successfully"},
        validation=True,
        access_role="Mechanic",
    ),
)
async def update_workshop_location(
    lat : float,
    lng : float,
    session : AsyncSession = Depends(get_async_session),
    mechanic : User = Depends(require_mechanic),
):
    try:
        mechanic.workshop_lat = lat
        mechanic.workshop_lng = lng       
        await session.commit()
        await session.refresh(mechanic)
        return {"message" : "Location updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500 , detail=str(e))






@router.patch(
    "/availabilty/me",
    status_code=200,
    summary="Update mechanic availability",
    description="""
Update the availability status of the authenticated mechanic.

- true → mechanic can receive new jobs
- false → mechanic will not receive new jobs

🔒 Mechanic authentication required
    """,
    responses=swagger_responses(
        success_message={"message":"Availabilty updated"},
        validation=True,
        access_role="Mechanic"
    ),
)
async def update_availabilty(
    availability: bool,
    session: AsyncSession = Depends(get_async_session),
    mechanic : User = Depends(require_mechanic)
):   
    try:
        mechanic.is_available = availability   
        await session.commit()
        await session.refresh(mechanic)
        return {"message": "Availabilty updated"}
    except Exception as e:
        raise HTTPException(status_code=500 , detail=str(e))






@router.post(
    "/skills/me",
    status_code=200,
    summary="Set mechanic skills",
    description="""
Assign skills to the authenticated mechanic.

Accepts a list of skill names and links them to the mechanic profile.

📌 Duplicate skills are not allowed.

🔒 Mechanic authentication required
    """,
    responses=swagger_responses(
        success_message={"message":"Skills set successfully"},
        bad_request_message="You already have this skill {skill name}",
        validation=True,
        access_role="Mechanic"
    ),
)
async def set_skils(
    skills_in : Set[SkillName] = Query(...),

    session: AsyncSession = Depends(get_async_session),
    cur_mechanic : User = Depends(require_mechanic)
):
        try:
            for skill in skills_in:
                    result = await session.execute(select(Skill).where(Skill.skill_name == skill))
                    r_skill = result.scalar_one_or_none()
                    result1 = await session.execute(select(MechanicSkill).where(MechanicSkill.mechanic_id == cur_mechanic.id , MechanicSkill.skill_id == r_skill.skill_id))
                    mech_skill = result1.scalar_one_or_none()
                    if mech_skill:
                        raise HTTPException(status_code=400 , detail= f"You already have this skill {skill}")
                    s_skill = MechanicSkill(
                        mechanic_id = cur_mechanic.id,
                        skill_id = r_skill.skill_id
                    )
                    session.add(s_skill)
                    await session.commit()              
            return {"message" : "skills set successfully"}
        except Exception as e:
                raise HTTPException(status_code=500 , detail= str(e))






@router.get(
    "/skills/me",
    status_code=200,
    summary="Get mechanic skills",
    description="""
Retrieve all skills associated with the authenticated mechanic.

Used for:
- Job matching
- Filtering mechanics by capability

🔒 Mechanic authentication required
    """,
    responses=swagger_responses(
        success_message={ "skills": [
            "skill1",
            "skill2",
            "skill3"
        ]},
        access_role="Mechanic"
    ),
)
async def get_mechanic_skills(
    cur_mechanic : User = Depends(require_mechanic),
    session : AsyncSession = Depends(get_async_session)
):
    try:
        return {"skills" : await get_mechanic_skills(cur_mechanic.id , session)}
    except Exception as e:
        raise HTTPException(status_code=500 , detail= str(e))




@router.patch(
    "/mechanic/live_location/{request_id}",
    status_code=200,
    summary="Update mechanic live location",
    description="""
Update the authenticated mechanic's live GPS location 
for their currently assigned service request.

Location update rules:
- Database is updated only if:
    • Mechanic moved ≥ 10 meters
    OR
    • 30 seconds passed since last update
- If mechanic is within arrival range of request location:
    • Request status is automatically updated to ARRIVED
    • WebSocket tracking is closed

Used for:
- Real-time tracking
- Automatic arrival detection

🔒 Mechanic authentication required
    """,
    responses=swagger_responses(
        success_message={
            "message": "Location processed",
            "arrived": False
        },
        access_role="Mechanic"
    ),
)
async def update_mechanic_location(
    request_id: int,
    lat: float,
    lng: float,
    db: AsyncSession = Depends(get_async_session),
    cur_mechanic: User = Depends(require_mechanic)
):

    result = await db.execute(
        select(ServiceRequest).where(
            ServiceRequest.request_id == request_id
        )
    )
    request = result.scalar_one_or_none()

    if not request or request.mechanic_id != cur_mechanic.id:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status != Status.accepted:
        raise HTTPException(status_code=400, detail="Tracking not active")


    result = await db.execute(
        select(LocationTracking).where(
            LocationTracking.request_id == request_id
        )
    )
    tracking = result.scalar_one_or_none()

    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking row not found")

    distance = haversine_distance(
        tracking.mechanic_lat,
        tracking.mechanic_lng,
        lat,
        lng
    )

    time_passed = (datetime.now(timezone.utc) - tracking.timestamp).total_seconds()

    if distance >= 10 or time_passed >= 30:
        tracking.mechanic_lat = lat
        tracking.mechanic_lng = lng
        tracking.timestamp = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(tracking)

    arrival_distance = haversine_distance(
        request.user_lat,
        request.user_lng,
        lat,
        lng,
        km = False
    )

    arrived = False

    if arrival_distance <= 25:
        request.status = Status.arrived
        await db.commit()
        arrived = True

    await manager.broadcast(
        request_id,
        {
            "request_id": request_id,
            "lat": lat,
            "lng": lng,
            "arrived" : arrived ,
            "timestamp": datetime.now().isoformat()  
        }
    )
    if arrived:
        connections = manager.active_connections.get(request_id, [])
        if request_id in connections:
            for connection in manager.active_connections[request_id]:
                await connection.close()
                
        manager.active_connections.pop(request_id, None)
    
    return {"message": "Location updated" , "arrived" : arrived}





async def get_mechanic_skills(mechanic_id, session):
    result = await session.execute(select(MechanicSkill).where(MechanicSkill.mechanic_id == mechanic_id))
    skills_id = [row[0] for row in result.all()]
    skill_id_list = []

    for skill in skills_id:
        skill_id_list.append(skill.skill_id)
    
    skills = []
    for id in skill_id_list:
        result = await session.execute(select(Skill).where(Skill.skill_id == id))
        skill1 = result.scalar_one_or_none()
        skills.append(skill1.skill_name)
    return skills

