import rx
import rx.operators as op
from rx.subject import Subject
from rx.disposable import Disposable
from contextvars import ContextVar
import wrapt

from .utils import dropargs

obs_ctx = ContextVar("obs_ctx", default={})
action_ctx = ContextVar("action_ctx", default={})

class ObservableValue():
    def __init__(self, initial_value=None):
        self.current_value = initial_value
        self.values = Subject()
        self.observers = []

    def set(self, value):
        self.current_value = value
        self.values.on_next(self.current_value)

        ctx = action_ctx.get()
        if "to_update" in ctx:
            for obs in self.observers:
                if obs not in ctx["to_update"]:
                    ctx["to_update"].append(obs)
        else:
            for obs in self.observers:
                obs.deliver_values()

    def get(self):
        ctx = obs_ctx.get()
        if "observer" in ctx and ctx["observer"] not in self.observers:
            observer = ctx["observer"]
            self.observers.append(observer)
            sub = self.values.subscribe(observer)
            def dispose():
                sub.dispose()
                self.observers.remove(observer)
            ctx["subs"].append(dispose)
        
        return self.current_value

class BufferedObserver():
    def __init__(self, func):
        self.values = Subject()
        self.boundaries = Subject()
        self.grouped_values = self.values.pipe(
            op.buffer(self.boundaries)
        )

        self.sub = self.grouped_values.subscribe(func)

    def deliver_values(self):
        self.boundaries.on_next(True)

    def __call__(self, value):
        self.values.on_next(value)

    def dispose(self):
        self.sub.dispose()

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
        "observer": BufferedObserver(dropargs(func)),
        "subs": []
    }

    def run_func():
        prev_ctx = obs_ctx.get()
        obs_ctx.set(ctx)
        func()
        obs_ctx.set(prev_ctx)

    def dispose():
        nonlocal ctx, func
        for dispose_sub in ctx["subs"]:
            dispose_sub()
        ctx["observer"].dispose()
        del ctx
        del func

    run_func()
    return Disposable(dispose)

def run_in_action(func):
    ctx = {
        "to_update": []
    }

    prev_ctx = action_ctx.get()
    action_ctx.set(ctx)
    val = func()
    action_ctx.set(prev_ctx)

    for obs in ctx["to_update"]:
        obs.deliver_values()

    del ctx
    return val

@wrapt.decorator
def action(wrapped, instance, args, kwargs):
    return run_in_action(lambda: wrapped(*args, **kwargs))