from typing import Coroutine
import aioreactive as rx
from aioreactive import AsyncAnonymousObserver
from aioreactive.subject import AsyncSubject
from expression.core import pipe
from contextvars import ContextVar
from asyncinit import asyncinit
from collections.abc import Awaitable
import wrapt

from ..utils import dropargs
from . import operators as ops

action_ctx = ContextVar("action_ctx", default={})

@asyncinit
class BufferedObserver():
    async def __init__(self, func):
        self.values = AsyncSubject()
        self.boundaries = AsyncSubject()
        self.grouped_values = await pipe(
            self.values,
            await ops.buffer(self.boundaries)
        )

        self.sub = await self.grouped_values.subscribe_async(AsyncAnonymousObserver(func))

    def deliver_values(self):
        return self.boundaries.asend(True)

    def asend(self, value):
        return self.values.asend(value)

    def dispose_async(self):
        return self.sub.dispose_async()

async def run_in_action(func):
    ctx = {
        "to_await": [],
        "to_deliver": []
    }

    prev_ctx = action_ctx.get()
    action_ctx.set(ctx)
    val = func()
    if isinstance(val, Awaitable):
        val = await val
    action_ctx.set(prev_ctx)

    for cr in ctx["to_await"]:
        await cr

    for obs in ctx["to_deliver"]:
        await obs.deliver_values()

    del ctx
    return val

@wrapt.decorator
def action(wrapped, instance, args, kwargs):
    return run_in_action(lambda: wrapped(*args, **kwargs))