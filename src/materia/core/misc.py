from typing import Optional, Self, Iterator, TypeVar, Callable, Any, ParamSpec
from functools import partial

T = TypeVar("T")
P = ParamSpec("P")


def optional(func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> Optional[T]:
    try:
        res = func(*args, **kwargs)
    except TypeError as e:
        raise e
    except Exception:
        return None
    return res


def optional_next(it: Iterator[T]) -> Optional[T]:
    return optional(next, it)


def optional_string(value: Any, format_string: Optional[str] = None) -> str:
    if value is None:
        return ""
    res = optional(str, value)
    if res is None:
        return ""
    return format_string.format(res)
