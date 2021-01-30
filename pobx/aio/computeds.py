from .observables import ObservableValue, autorun
from .actions import action
from ..utils import to_async

def computed(func):
    @action
    async def call_func():
        return_val = await func()
        return_obs.set(return_val)

    sub = None
    async def on_start():
        nonlocal sub
        sub = await autorun(call_func)
    async def on_stop():
        await sub.dispose_async()

    return_obs = ObservableValue(None, on_start, on_stop)
    return return_obs

class ComputedProperty():
    def __init__(self, func):
        self.func = func

    def __set_name__(self, objtype, name):
        self.name = name
        self.attr = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if not hasattr(obj, self.attr):
            setattr(obj, self.attr, computed(lambda: self.func(obj)))
        obs = getattr(obj, self.attr)
        return obs.get()

def computedproperty(func):
    return ComputedProperty(func)

computed_property = computedproperty