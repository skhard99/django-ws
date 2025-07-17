from channels.generic.websocket import AsyncWebsocketConsumer
import json
import uuid
import time
from chat.connection_pool import active_connections
from chat.session_store import TTLSessionStore
import logging
from chat.metrics import (
    inc_connections, set_active_connections, inc_messages, 
    record_message_processing_time
)

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
        
        # Update Prometheus metrics
        inc_connections()
        set_active_connections(len(active_connections))
        
        logging.info("Client connected", extra={
            "session_id": self.session_id,
            "resumed": bool(saved),
            "count": self.count,
            "total_active": len(active_connections)
        })

    async def receive(self, text_data):
        # Record message processing time
        start_time = time.time()
        
        try:
            if text_data == "exit":
                await self.send(text_data=json.dumps({"bye": True, "total": self.count}))
                await self.close(code=1001)
                return
            
            self.active += 1
            self.count += 1
            
            # Update Prometheus metrics
            inc_messages()
            
            await self.send(text_data=json.dumps({"count": self.count}))
            
        finally:
            self.active -= 1
            
            # Record processing time
            processing_time = time.time() - start_time
            record_message_processing_time(processing_time)

    async def disconnect(self, close_code):
        self.closed = True
        
        # Remove from active connections
        active_connections.discard(self)
        
        # Update metrics
        set_active_connections(len(active_connections))
        
        if self.session_id:
            session_store.set(self.session_id, {"count": self.count})
        
        logging.info("Client disconnected", extra={
            "session_id": self.session_id,
            "total_messages": self.count,
            "close_code": close_code,
            "remaining_active": len(active_connections)
        })