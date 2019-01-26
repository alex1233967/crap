#!/usr/bin/python3
from functools import update_wrapper

callcounts = {}


def decorator(d):
    """Make function d a decorator: d wraps a function fn."""
    def _d(fn):
        return update_wrapper(d(fn), fn)
    update_wrapper(_d, d)
    return _d


@decorator
def memo(f):
    """Decorator that caches the return value for each call to f(args).
    Then when called again with same args, we c an just look it up."""
    cache = {}

    def f_wrapper(*args):
        try:
            return cache[args]
        except KeyError:
            cache[args] = result = f(*args)
            return result
        except TypeError:
            return f(*args)
    update_wrapper(f_wrapper, f)
    return f_wrapper


@decorator
def countcalls(f):
    """Decorator that makes the function count calls to it, in callcounts[f]."""
    def _f(*args):
        callcounts[_f] += 1
        return f(*args)
    callcounts[_f] = 0
    return _f


@decorator
def trace(f):
    indent = '   '

    def _f(*args):
        signature = '{}({})'.format(f.__name__, ', '.join(map(repr, args)))
        print('{}--> {}'.format(trace.level*indent, signature))
        trace.level += 1
        try:
            result = f(*args)
            print('{}<-- {} == {}'.format((trace.level-1)*indent,
                                          signature, result))
        finally:
            trace.level -= 1
        return result
    trace.level = 0
    return _f


@trace
@memo
@countcalls
def fib(n):
    """Calculate n-th Fibonacci number."""
    if n <= 1:
        return 1
    return fib(n - 1) + fib(n - 2)


if __name__ == "__main__":
    print(fib.__doc__)
    print(fib(10))
    print(callcounts)
