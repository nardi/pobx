import rx
import rx.operators as op
from rx.subject import Subject
from rx.disposable import Disposable
from contextvars import ContextVar
import wrapt

from .utils import dropargs

action_ctx = ContextVar("action_ctx", default={})

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