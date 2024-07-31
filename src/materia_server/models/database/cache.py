from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Self
from pydantic import BaseModel, RedisDsn
from redis import asyncio as aioredis
from redis.asyncio.client import Pipeline

class CacheError(Exception):
    pass 

class Cache:
    def __init__(self, url: RedisDsn, pool: aioredis.ConnectionPool):
        self.url: RedisDsn = url 
        self.pool: aioredis.ConnectionPool = pool

    @staticmethod
    async def new(
            url: RedisDsn, 
            encoding: str = "utf-8", 
            decode_responses: bool = True,
            test_connection: bool = True
        ) -> Self:
        pool = aioredis.ConnectionPool.from_url(str(url), encoding = encoding, decode_responses = decode_responses)

        if test_connection:
            try:
                connection = pool.make_connection()
                await connection.connect()
            except ConnectionError as e:
                raise CacheError(f"{e}") 
            else:
                await connection.disconnect()

        return Cache(
            url = url, 
            pool = pool
        )

    @asynccontextmanager 
    async def client(self) -> AsyncGenerator[aioredis.Redis, Any]: 
        try:
            yield aioredis.Redis(connection_pool = self.pool)
        except Exception as e:
            raise CacheError(f"{e}")

    @asynccontextmanager 
    async def pipeline(self, transaction: bool = True) -> AsyncGenerator[Pipeline, Any]:
        client = await aioredis.Redis(connection_pool = self.pool)

        try:
            yield client.pipeline(transaction = transaction)
        except Exception as e:
            raise CacheError(f"{e}")
    
