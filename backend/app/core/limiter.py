from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate-limiter instance used across the application.
limiter = Limiter(key_func=get_remote_address)
