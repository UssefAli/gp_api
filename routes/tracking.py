from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.db.models import ServiceRequest, User, get_async_session
from dependencies.helper import Status
from dependencies.permissions import require_user, require_user_ws
from services.webscoket_manager import manager
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.websocket("/ws/requests/{request_id}")
async def websocket_tracking(websocket: WebSocket, request_id: int , cur_user : User = Depends(require_user_ws) , session : AsyncSession = Depends(get_async_session)):

    """
    Real-time tracking WebSocket endpoint.

    Connect to receive live mechanic location updates 
    for a specific service request.

    WebSocket Events:
    - Receives JSON messages:
        {
            "request_id": 1,
            "lat": 30.1234,
            "lng": 31.5678,
            "arrived": false,
            "timestamp": "ISO_DATETIME"
        }

    Connection Rules:
    - Only the owner of the request can connect
    - Request must be in ACCEPTED status
    - Connection automatically closes when mechanic arrives

    🔒 User authentication required (Bearer token in headers)
    """

    result = await session.execute(select(ServiceRequest).where(ServiceRequest.request_id == request_id))
    request = result.scalar_one_or_none()
    if not request or request.user_id != cur_user.id:
        await websocket.close(code=1008)
        return

    if request.status not in (Status.accepted):
        await websocket.close(code=1008)
        return
      
    await manager.connect(request_id, websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(request_id, websocket)
