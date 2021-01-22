from .observables import ObservableValue, autorun

def computed(func):
    def call_func():
        return_val = func()
        return_obs.set(return_val)

    sub = None
    def on_start():
        nonlocal sub
        sub = autorun(call_func)
    def on_stop():
        sub.dispose()

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