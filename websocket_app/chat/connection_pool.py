import asyncio
import json
from datetime import datetime, timezone
from chat.metrics import inc_heartbeat_pings, set_active_connections

active_connections = set()

async def heartbeat():
    """Send heartbeat to all active connections every 30 seconds"""
    while True:
        await asyncio.sleep(30)
        timestamp = datetime.now(timezone.utc).isoformat()
        message = json.dumps({
            "type": "heartbeat",
            "timestamp": timestamp,
            "active_connections": len(active_connections)
        })
        
        stale_connections = []
        successful_pings = 0

        for conn in active_connections:
            try:
                await conn.send(text_data=message)
                successful_pings += 1
                inc_heartbeat_pings()
            except Exception as e:
                print(f"Heartbeat failed for connection {getattr(conn, 'session_id', 'unknown')}: {e}")
                stale_connections.append(conn)

        # Remove stale connections
        for conn in stale_connections:
            active_connections.discard(conn)
        
        # Update active connections metric
        set_active_connections(len(active_connections))
        
        print(f"Heartbeat sent to {successful_pings} connections, removed {len(stale_connections)} stale connections")

def get_connection_stats():
    """Get current connection statistics"""
    return {
        "active_connections": len(active_connections),
        "connection_objects": [
            {
                "session_id": getattr(conn, 'session_id', 'unknown'),
                "message_count": getattr(conn, 'count', 0),
                "active": not getattr(conn, 'closed', True)
            }
            for conn in active_connections
        ]
    }