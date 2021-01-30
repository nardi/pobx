import aioreactive as rx
from aioreactive import AsyncAnonymousObserver
from aioreactive.subject import AsyncSubject

from ..utils import dropargs, asyncinit

@asyncinit
class BufferOperator():
    async def __init__(self, boundaries):
        self.emitter = AsyncSubject()
        self.buffer = []

        async def emit_buffer():
            buffer = self.buffer
            self.buffer = []
            await self.emitter.asend(buffer)

        self.subs = [
            await boundaries.subscribe_async(AsyncAnonymousObserver(dropargs(emit_buffer)))
        ]

    async def __call__(self, receiver):
        async def add_to_buffer(x):
            self.buffer.append(x)

        self.subs.append(await receiver.subscribe_async(AsyncAnonymousObserver(add_to_buffer)))
        return self

    async def subscribe_async(self, *args, **kwargs):
        return await self.emitter.subscribe_async(*args, **kwargs)

    async def dispose_async(self):
        for sub in self.subs:
            await sub.dispose_async()
        self.buffer.clear()

async def buffer(boundaries):
    return await BufferOperator(boundaries)