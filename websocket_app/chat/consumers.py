from channels.generic.websocket import AsyncWebsocketConsumer
import json
import uuid
from chat.connection_pool import active_connections
from chat.session_store import TTLSessionStore
import logging
from chat.metrics import inc, set_value

session_store = TTLSessionStore()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.count = 0
        self.active = 0
        self.closed = False
        # Get WebSocket key from scope headers
        headers = dict(self.scope["headers"])
        session_id = headers.get(b'x-session-id')  # header keys are lowercase and bytes
        self.session_id = session_id.decode() if session_id else str(uuid.uuid4())

        # Try to restore previous state
        saved = session_store.get(self.session_id)
        self.count = saved.get("count", 0) if saved else 0

        await self.accept()
        await self.send(text_data=json.dumps({
            "session_id": self.session_id,  # Send back new or existing session ID
            "resumed": bool(saved),
            "count": self.count
        }))

        active_connections.add(self)
        logging.info("Client connected", extra={
            "session_id": self.session_id,
            "resumed": bool(saved),
            "count": self.count
        })
        inc("total_connections")
        set_value("connected_users", len(active_connections))

    async def receive(self, text_data):
        if text_data == "exit":
            await self.send(text_data=json.dumps({"bye": True, "total": self.count}))
            await self.close(code=1001)
            return
        self.active += 1
        inc("total_messages")
        try:

            self.count += 1
            await self.send(text_data=json.dumps({"count": self.count}))
        finally:
            self.active -= 1

    async def disconnect(self, close_code):
        self.closed = True
        if self.session_id:
            session_store.set(self.session_id, {"count": self.count})
        logging.info("Client disconnected", extra={
            "session_id": self.session_id,
            "total_messages": self.count
        })
        set_value("connected_users", len(active_connections) - 1)
        #active_connections.discard(self)
        pass
