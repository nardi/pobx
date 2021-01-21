import rx
from rx.subject import Subject
from rx.disposable import Disposable
from contextvars import ContextVar

from .actions import action_ctx, BufferedObserver
from .utils import dropargs

obs_ctx = ContextVar("obs_ctx", default={})

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
            ctx["subs"].append(Disposable(dispose))
        
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
        for sub in ctx["subs"]:
            sub.dispose()
        ctx["observer"].dispose()
        del ctx
        del func

    run_func()
    return Disposable(dispose)
