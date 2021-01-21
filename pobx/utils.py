import wrapt

@wrapt.decorator
def dropargs(wrapped, instance, args, kwargs):
    return wrapped()