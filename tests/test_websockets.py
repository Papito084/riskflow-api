import uuid

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.main import app
from src.services.websocket_manager import ConnectionManager


def test_websocket_connection_and_handshake():
    client = TestClient(app)
    account_id = uuid.uuid4()

    with client.websocket_connect(f"/api/v1/ws/accounts/{account_id}") as websocket:
        # First message is the connection confirmation
        data = websocket.receive_json()
        assert data["event_type"] == "CONNECTED"
        assert data["account_id"] == str(account_id)

        # Send ping, expect pong
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"


def test_websocket_invalid_token_rejected():
    client = TestClient(app)
    account_id = uuid.uuid4()

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/api/v1/ws/accounts/{account_id}?token=invalid-token"):
            pass


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    manager = ConnectionManager()
    account_id = uuid.uuid4()

    class MockWebSocket:
        def __init__(self) -> None:
            self.accepted = False
            self.sent_messages: list[str] = []

        async def accept(self) -> None:
            self.accepted = True

        async def send_text(self, text: str) -> None:
            self.sent_messages.append(text)

    mock_ws = MockWebSocket()
    await manager.connect(account_id, mock_ws)  # type: ignore[arg-type]

    assert account_id in manager.active_connections
    assert len(manager.active_connections[account_id]) == 1

    # Broadcast message
    test_message = {"event": "TEST_ALERT", "value": 123}
    await manager.broadcast_to_account(account_id, test_message)

    assert len(mock_ws.sent_messages) == 1
    assert "TEST_ALERT" in mock_ws.sent_messages[0]

    # Disconnect
    await manager.disconnect(account_id, mock_ws)  # type: ignore[arg-type]
    assert account_id not in manager.active_connections
