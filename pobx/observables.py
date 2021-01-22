import rx
from rx.subject import Subject
from rx.disposable import Disposable
from contextvars import ContextVar
import wrapt

from .actions import action_ctx, BufferedObserver
from .utils import dropargs, noop

obs_ctx = ContextVar("obs_ctx", default={})

class ObservableValue():
    def __init__(self, initial_value=None, on_start=noop, on_stop=noop):
        self.current_value = initial_value
        self.values = Subject()
        self.observers = {}
        self.on_start = on_start
        self.on_stop = on_stop

    def set(self, value):
        if self.current_value != value:
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
        if "observer" in ctx:
            observer = ctx["observer"]
            if not self.observers:
                self.on_start()
            if observer not in self.observers:
                sub = self.values.subscribe(observer)
                def dispose():
                    sub.dispose()
                    del self.observers[observer]
                    if not self.observers:
                        self.on_stop()
                self.observers[observer] = Disposable(dispose)
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

def autorun(func):
    def run_func():
        # TODO: write unit test for conditional observer. Something like:
        # if pair.y > 10:
        #   print(pair.x)
        # and then change x when y is less than 10.
        prev_subs = ctx["subs"]
        ctx["subs"] = set()

        parent_ctx = obs_ctx.get()
        obs_ctx.set(ctx)
        func()
        obs_ctx.set(parent_ctx)

        for sub in prev_subs - ctx["subs"]:
            sub.dispose()

    ctx = {
        "observer": BufferedObserver(dropargs(run_func)),
        "subs": set()
    }

    def dispose():
        nonlocal ctx, func
        for sub in ctx["subs"]:
            sub.dispose()
        ctx["observer"].dispose()
        del ctx
        del func

    run_func()    

    sub = Disposable(dispose)
    return sub
