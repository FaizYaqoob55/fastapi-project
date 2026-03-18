import json
import os
import functools
import time
from typing import Any, Callable
import redis
from datetime import timedelta
from fastapi import Request
from sqlalchemy.orm import Session

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    socket_connect_timeout=0.5,
    socket_timeout=0.5
)

# Circuit Breaker for Redis
REDIS_CIRCUIT_BREAKER_OPEN_UNTIL = 0
CIRCUIT_BREAKER_COOLDOWN = 60  # seconds

def cache_response(expire: int = 300):
    """
    Decorator to cache FastAPI response data in Redis.
    Args:
        expire: Expiration time in seconds (default 5 minutes).
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate a unique cache key based on function name and arguments
            # We filter out non-serializable arguments like Request, Session, or current_user
            cache_args = {}
            for k, v in kwargs.items():
                if isinstance(v, (Request, Session)):
                    continue
                if k == "current_user":
                    continue
                # Also ignore anything that looks like an ORM model
                if hasattr(v, "_sa_instance_state"):
                    continue
                cache_args[k] = v
            
            # If current_user is passed, include their ID in the key
            user_id = ""
            if "current_user" in kwargs and hasattr(kwargs["current_user"], "id"):
                user_id = f":user_{kwargs['current_user'].id}"
            
            key = f"dashboard:{func.__name__}{user_id}:{json.dumps(cache_args, sort_keys=True)}"
            
            global REDIS_CIRCUIT_BREAKER_OPEN_UNTIL
            
            # Check circuit breaker
            if time.time() < REDIS_CIRCUIT_BREAKER_OPEN_UNTIL:
                return func(*args, **kwargs)
            
            # Check Redis for existing cache
            try:
                cached_data = redis_client.get(key)
                if cached_data:
                    return json.loads(cached_data)
            except redis.RedisError:
                # If Redis is down, fail gracefully and open the circuit breaker
                REDIS_CIRCUIT_BREAKER_OPEN_UNTIL = time.time() + CIRCUIT_BREAKER_COOLDOWN
                return func(*args, **kwargs)

            # Execute the function
            result = func(*args, **kwargs)

            # Store the result in Redis
            try:
                redis_client.setex(
                    key,
                    timedelta(seconds=expire),
                    json.dumps(result)
                )
            except redis.RedisError:
                # If Redis is down, open the circuit breaker
                REDIS_CIRCUIT_BREAKER_OPEN_UNTIL = time.time() + CIRCUIT_BREAKER_COOLDOWN

            return result
        return wrapper
    return decorator
