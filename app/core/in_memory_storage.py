import logging
from datetime import datetime, timedelta

from app.core.storage import CaptchaStorage

logger=logging.getLogger(__name__)
class MemoryStorage(CaptchaStorage):
    def __init__(self):
        self._storage = {}
    async def set(self,key,code,ttl):
        expire_at=datetime.now()+timedelta(seconds=ttl)
        self._storage[key]={'captcha_code':code,
            'expires_at':expire_at}
        logger.info(self._storage)

    async def get(self,key):
        if key not in self._storage:
            return None
        data=self._storage[key]
        logger.info('code,expire at',data)
        if datetime.now()>data['expires_at']:
            self._storage.pop(key,None)
            return None
        return data['captcha_code']
    async def delete(self,key):
        self._storage.pop(key,None)

