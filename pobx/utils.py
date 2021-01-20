def dropargs(func):
    def wrapper(*args, **kwargs):
        return func()
    return wrapper