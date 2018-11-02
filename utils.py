import os
import time
from functools import wraps


def jj(*args):
    return os.path.join(*args)


class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs


def profile(fn):
    @wraps(fn)
    def with_profiling(*args, **kwargs):
        with Timer() as t:
            ret = fn(*args, **kwargs)

        return ret, t.secs

    return with_profiling
