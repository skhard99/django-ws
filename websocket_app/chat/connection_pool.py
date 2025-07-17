import asyncio
import json
from datetime import datetime, timezone
from chat.metrics import inc

active_connections = set()

async def heartbeat():
    while True:
        await asyncio.sleep(30)
        timestamp = datetime.now(timezone.utc).isoformat()
        message = json.dumps({"ts": timestamp})
        stale_connections = []

        for conn in active_connections:
            try:
                print(message)
                inc("heartbeat_pings")
                await conn.send(text_data=message)
            except Exception:
                stale_connections.append(conn)

        for conn in stale_connections:
            active_connections.discard(conn)