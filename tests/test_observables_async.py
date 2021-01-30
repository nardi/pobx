from .context import pobx
import pytest

from pobx.aio import observables, autorun, action, computed, computedproperty, run_in_action
from pobx.utils import asyncinit

@asyncinit
class Pair():
    x, y = observables(2)
    
    async def __init__(self, x, y):
        await self.update(x, y)

    @action
    async def update(self, x, y):
        self.x = x
        self.y = y

    @computedproperty
    async def diff(self):
        return await self.y - await self.x

called_print_diff = 0

async def print_diff(pair):
    global called_print_diff
    print(f"x={await pair.x}, y={await pair.y}")
    print("Difference:", await pair.y - await pair.x)
    called_print_diff += 1

@pytest.mark.asyncio
async def test_autorun_action():
    global called_print_diff

    print("Testing autorun with actions")

    pair = await Pair(5, 10)

    called_print_diff = 0

    diff = await autorun(lambda: print_diff(pair))

    @action
    def set_values():
        pair.x = 4
        pair.y = 2
    await set_values()

    await pair.update(6, 10)

    await diff.dispose_async()

    def assign(): pair.y = 12
    await run_in_action(assign)    

    print(f"Final: x={await pair.x}, y={await pair.y}")

    assert await pair.x == 6
    assert await pair.y == 12
    assert called_print_diff == 3

@pytest.mark.asyncio
async def test_autorun_computed():
    print("Testing autorun with computed function")

    pair = await Pair(5, 7)

    called_diff = 0

    @computed
    async def diff():
        nonlocal called_diff
        called_diff += 1
        return await pair.y - await pair.x

    called_print_diff = 0

    async def print_diff():
        nonlocal called_print_diff
        print("Difference:", await diff.get())
        called_print_diff += 1
    sub = await autorun(print_diff)
    assert called_diff == 1
    assert called_print_diff == 1

    @action
    def set_values():
        pair.x = 4
        pair.y = 2
    await set_values()
    assert called_diff == 2
    assert called_print_diff == 2

    await pair.update(10, 8)
    assert called_diff == 3
    assert called_print_diff == 2

    await sub.dispose_async()
    # After this diff is no longer being used, so no reason to recalculate
    # the value when y changes.
    def assign(): pair.y = 12
    await run_in_action(assign)

    print(f"Final: x={await pair.x}, y={await pair.y}")

    assert await pair.x == 10
    assert await pair.y == 12
    assert called_diff == 3
    assert called_print_diff == 2

@pytest.mark.asyncio
async def test_autorun_computedproperty():
    print("Testing autorun with computed property")

    pair = await Pair(5, 7)

    called_print_diff = 0

    async def print_diff():
        nonlocal called_print_diff
        print("Difference:", await pair.diff)
        called_print_diff += 1
    sub = await autorun(print_diff)
    assert called_print_diff == 1

    @action
    def set_values():
        pair.x = 4
        pair.y = 2
    await set_values()
    assert called_print_diff == 2

    await pair.update(10, 8)
    assert called_print_diff == 2

    await sub.dispose_async()

    def assign(): pair.y = 12
    await run_in_action(assign)

    print(f"Final: x={await pair.x}, y={await pair.y}")

    assert await pair.x == 10
    assert await pair.y == 12
    assert called_print_diff == 2
