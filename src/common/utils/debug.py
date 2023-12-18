import time
from functools import wraps


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        execution_time = time.perf_counter() - start_time
        print(f"{func.__name__}: {execution_time:.2f}")
        return result

    return wrapper


def async_timer(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        execution_time = time.perf_counter() - start_time
        print(f"{func.__name__}: {execution_time:.4f}")
        return result

    return wrapper
