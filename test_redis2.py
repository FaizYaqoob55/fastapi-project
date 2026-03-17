import time
from app.utils.cache import redis_client
import redis

print("Testing Redis Connection...")
redis_client = redis.Redis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)
start = time.time()
try:
    res = redis_client.get('test_key')
    print(f"Result: {res}")
except redis.RedisError as e:
    print(f"RedisError: {e}")
except Exception as e:
    print(f"Other Error: {e}")
finally:
    end = time.time()
    print(f"Time taken: {end - start:.2f} seconds")
