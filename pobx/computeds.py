from .observables import ObservableValue, autorun

def computed(func, _self=None):
    return_observable = ObservableValue()
    def call_func():
        return func(_self) if _self else func()
    autorun(call_func, return_observable)
    return return_observable

class ComputedProperty():
    def __init__(self, func):
        self.func = func

    def __set_name__(self, objtype, name):
        self.name = name
        self.attr = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if not hasattr(obj, self.attr):
            setattr(obj, self.attr, computed(self.func, obj))
        obs = getattr(obj, self.attr)
        return obs.get()

def computedproperty(func):
    return ComputedProperty(func)

computed_property = computedproperty