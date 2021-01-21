from .context import pobx
import pytest

from pobx import observables, autorun, action

class Pair():
    x, y = observables(2)
    
    def __init__(self, x, y):
        self.update(x, y)

    @action
    def update(self, x, y):
        self.x = x
        self.y = y

called_print_diff = 0

def print_diff(pair):
    global called_print_diff
    print(f"x={pair.x}, y={pair.y}")
    print("Difference:", pair.y - pair.x)
    called_print_diff += 1

def test_autorun_object():
    global called_print_diff

    print("Testing autorun with plain assignment")

    pair = Pair(5, 10)

    called_print_diff = 0

    diff = autorun(lambda: print_diff(pair))

    pair.x = 4
    pair.y = 2

    pair.x = 6
    pair.y = 10

    diff.dispose()

    pair.y = 12

    print(f"Final: x={pair.x}, y={pair.y}")

    assert pair.x == 6
    assert pair.y == 12
    assert called_print_diff == 5

def test_autorun_action():
    global called_print_diff

    print("Testing autorun with actions")

    pair = Pair(5, 10)

    called_print_diff = 0

    diff = autorun(lambda: print_diff(pair))

    @action
    def set_values():
        pair.x = 4
        pair.y = 2
    set_values()

    pair.update(6, 10)

    diff.dispose()

    pair.y = 12

    print(f"Final: x={pair.x}, y={pair.y}")

    assert pair.x == 6
    assert pair.y == 12
    assert called_print_diff == 3
