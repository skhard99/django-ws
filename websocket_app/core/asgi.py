"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
log_handler = logging.StreamHandler()

formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
log_handler.setFormatter(formatter)

logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.connection_pool import heartbeat
from chat.connection_pool import active_connections
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from chat.routing import websocket_urlpatterns
from chat.connection_pool import heartbeat
import asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

asyncio.get_event_loop().create_task(heartbeat())

routes = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})

from datetime import datetime
import json

class LifespanApp:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    print("[Shutdown] Closing WebSocket connections...")
                    print(f"[shutdown] Pool size: {len(active_connections)}")
                    tasks = []

                    for conn in list(active_connections):
                        try:
                            # Wait for in-flight messages
                            for _ in range(100):
                                if getattr(conn, "active", 0) == 0:
                                    break
                                await asyncio.sleep(0.1)

                            if getattr(conn, "closed", False):
                                print("Connection already closed. Skipping close.")
                                continue

                            await conn.send(text_data=json.dumps({
                                "bye": True,
                                "total": getattr(conn, "count", 0)
                            }))
                            await conn.close(code=1001)

                        except Exception as e:
                            print(f"Failed to close conn: {e}")

                    await send({"type": "lifespan.shutdown.complete"})
                    return
        else:
            await self.app(scope, receive, send)


application = LifespanApp(routes)

