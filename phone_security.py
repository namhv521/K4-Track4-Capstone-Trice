"""Session-scoped producer capability; tokens live only in RAM."""
import ipaddress
import secrets
from time import monotonic


def is_loopback(host):
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class PairingTokens:
    def __init__(self, ttl=600, clock=monotonic):
        self.ttl, self.clock, self.entries = ttl, clock, {}

    def issue(self, session_id):
        token = secrets.token_urlsafe(32)
        self.entries[session_id] = (token, self.clock() + self.ttl)
        return token

    def valid(self, session_id, token):
        entry = self.entries.get(session_id)
        return bool(entry and self.clock() < entry[1] and isinstance(token, str)
                    and secrets.compare_digest(entry[0], token))

    def touch(self, session_id):
        if session_id in self.entries:
            token, _ = self.entries[session_id]
            self.entries[session_id] = (token, self.clock() + self.ttl)

    def revoke(self, session_id):
        self.entries.pop(session_id, None)
