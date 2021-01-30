import aioreactive as rx
from aioreactive.subject import AsyncSubject
from asyncinit import asyncinit
from contextvars import ContextVar
from expression.system import AsyncDisposable

from .actions import action_ctx, BufferedObserver
from ..utils import dropargs, noop, noop_async

obs_ctx = ContextVar("obs_ctx", default={})

class ObservableValue():
    def __init__(self, initial_value=None, on_start=noop_async, on_stop=noop_async):
        self.current_value = initial_value
        self.values = AsyncSubject()
        self.observers = {}
        self.on_start = on_start
        self.on_stop = on_stop

    def set(self, value):
        if self.current_value != value:
            self.current_value = value

            ctx = action_ctx.get()

            if not ctx:
                raise Exception("Cannot change observable outside of action.")

            if "to_await" in ctx:
                ctx["to_await"].append(self.values.asend(self.current_value))
            if "to_deliver" in ctx:
                for obs in self.observers:
                    if obs not in ctx["to_deliver"]:
                        ctx["to_deliver"].append(obs)

    async def get(self):
        ctx = obs_ctx.get()
        if "observer" in ctx:
            observer = ctx["observer"]
            if not self.observers:
                await self.on_start()
            if observer not in self.observers:
                sub = await self.values.subscribe_async(observer)
                async def dispose_async():
                    await sub.dispose_async()
                    del self.observers[observer]
                    if not self.observers:
                        await self.on_stop()
                self.observers[observer] = AsyncDisposable.create(dispose_async)
            ctx["subs"].add(self.observers[observer])
        
        return self.current_value

class ObservableProperty():
    def __set_name__(self, objtype, name):
        self.name = name
        self.attr = f"_{name}"
    
    def __set__(self, obj, value):
        if not hasattr(obj, self.attr):
            setattr(obj, self.attr, ObservableValue(value))
        else:
            obs = getattr(obj, self.attr)
            obs.set(value)
    
    def __get__(self, obj, objtype=None):
        obs = getattr(obj, self.attr)
        return obs.get()

class ObservableFactory():
    def __call__(self):
        return ObservableProperty()

    def box(value):
        return ObservableValue(value)

observable = ObservableFactory()

def observables(n):
    return tuple(map(lambda _: observable(), range(n)))

async def autorun(func):
    async def run_func():
        # TODO: write unit test for conditional observer. Something like:
        # if pair.y > 10:
        #   print(pair.x)
        # and then change x when y is less than 10.
        prev_subs = ctx["subs"]
        ctx["subs"] = set()

        parent_ctx = obs_ctx.get()
        obs_ctx.set(ctx)
        await func()
        obs_ctx.set(parent_ctx)

        for sub in prev_subs - ctx["subs"]:
            await sub.dispose_async()

    ctx = {
        "observer": await BufferedObserver(dropargs(run_func)),
        "subs": set()
    }

    async def dispose_async():
        nonlocal ctx, func
        for sub in ctx["subs"]:
            await sub.dispose_async()
        await ctx["observer"].dispose_async()
        del ctx
        del func

    await run_func()    

    sub = AsyncDisposable.create(dispose_async)
    return sub