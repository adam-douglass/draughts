from functools import wraps


def memoize(function):
    """A simple closure that ensures all calls identical to a function have the same return."""
    memo = {}

    @wraps(function)
    def _memoized(*args):
        if args not in memo:
            value = memo[args] = function(*args)
            return value
        return memo[args]

    return _memoized


def memoize_on_first(function):
    """A simple closure that ensures all calls identical to a function have the same return."""
    memo = {}

    @wraps(function)
    def _memoized(first, *args):
        if first not in memo:
            value = memo[first] = function(first, *args)
            return value
        return memo[first]

    return _memoized
