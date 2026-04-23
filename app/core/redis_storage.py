import redis.asyncio as redis
from app.core.storage import CaptchaStorage
class RedisStorage(CaptchaStorage):
    def __init__(self,redis_client:redis.Redis):
        self.client=redis_client

    async def get(self,key):

        result=await self.client.get(f"captcha:{key}")
        return result if result else None
    async def set(self,key,code,ttl):
        await self.client.setex(f"captcha:{key}",ttl,code)

    async def delete(self,key):
        await  self.client.delete(f"captcha:{key}")
