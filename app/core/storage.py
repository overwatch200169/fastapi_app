from abc import ABC,abstractmethod

class CaptchaStorage(ABC):
    @abstractmethod
    async def get(self,key):...

    @abstractmethod
    async def set(self,key,code,ttl):...

    @abstractmethod
    async def delete(self,key):...


