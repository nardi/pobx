import wrapt
from asyncinit import asyncinit

@wrapt.decorator
def dropargs(wrapped, instance, args, kwargs):
    return wrapped()

def noop(*args, **kwargs):
    pass

async def noop_async(*args, **kwargs):
    pass

@wrapt.decorator
async def to_async(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)