import rx
from rx.subject import Subject
from rx.disposable import Disposable
from contextvars import ContextVar

from .utils import dropargs

obs_ctx = ContextVar("obs_ctx", default={})

class ObservableValue():
    def __init__(self, initial_value=None):
        self.current_value = initial_value
        self.values = Subject()

        def update(value):
            self.current_value = value
        self.values.subscribe(
            on_next=update
        )

    def set(self, value):
        self.values.on_next(value)

    def get(self):
        ctx = obs_ctx.get()
        if "observer" in ctx and "subs" in ctx and self.values not in ctx["subs"]:
            ctx["subs"][self.values] = self.values.subscribe(ctx["observer"])
        
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

def autorun(func):
    ctx = {
        "observer": dropargs(func),
        "subs": {}
    }

    def run_func():
        prev_ctx = obs_ctx.get()
        obs_ctx.set(ctx)
        func()
        obs_ctx.set(prev_ctx)

    def dispose():
        nonlocal ctx, func
        for sub in ctx["subs"].values():
            sub.dispose()
        del func
        del ctx

    run_func()
    return Disposable(dispose)