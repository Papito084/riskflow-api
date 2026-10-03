import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import decode_token
from src.repositories.account_repository import AccountRepository
from src.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSockets"])


@router.websocket("/accounts/{account_id}")
async def account_events_websocket(
    websocket: WebSocket,
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    token: str | None = Query(None),
) -> None:
    # Optional JWT validation if token is provided
    if token:
        try:
            payload = decode_token(token)
            user_id = uuid.UUID(payload.get("sub", ""))
            account_repo = AccountRepository(session)
            account = await account_repo.get_by_id(account_id)
            if not account or account.user_id != user_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except Exception as e:
            logger.warning("WebSocket auth failed for account %s: %s", account_id, e)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws_manager.connect(account_id, websocket)
    try:
        # Send initial confirmation handshake
        await websocket.send_json(
            {
                "event_type": "CONNECTED",
                "account_id": str(account_id),
                "message": f"Successfully subscribed to real-time events for account {account_id}",
            }
        )

        while True:
            # Keep socket alive and allow client to send heartbeats/ping
            data = await websocket.receive_text()
            if data.lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(account_id, websocket)
    except Exception as e:
        logger.warning("WebSocket error on account %s: %s", account_id, e)
        await ws_manager.disconnect(account_id, websocket)
