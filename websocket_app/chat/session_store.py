import time
from collections import OrderedDict

class TTLSessionStore:
    def __init__(self, ttl_seconds=300):
        self.ttl = ttl_seconds
        self.sessions = OrderedDict()

    def set(self, session_id, data):
        self.sessions[session_id] = (time.time(), data)

    def get(self, session_id):
        entry = self.sessions.get(session_id)
        if not entry:
            return None
        created_at, data = entry
        if time.time() - created_at > self.ttl:
            del self.sessions[session_id]
            return None
        return data

    def delete(self, session_id):
        self.sessions.pop(session_id, None)
