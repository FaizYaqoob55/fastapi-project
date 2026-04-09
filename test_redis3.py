import time
from app.utils.cache import redis_client
import redis

print("Testing Redis Connection...")
redis_client = redis.Redis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True,
    socket_connect_timeout=0.5,
    socket_timeout=0.5
)
start = time.time()
try:
    res = redis_client.get('test_key')
except redis.RedisError as e:
    pass
end1 = time.time()
try:
    redis_client.setex('test_key', 10, 'val')
except redis.RedisError as e:
    pass
end2 = time.time()
print(f"Time taken 1: {end1 - start:.2f} seconds")
print(f"Time taken 2: {end2 - end1:.2f} seconds")
 