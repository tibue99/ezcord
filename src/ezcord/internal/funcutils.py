from typing import Any, Callable, ParamSpec, TypeVar, cast

P = ParamSpec("P")
T = TypeVar("T")


def copy_kwargs(kwargs_call: Callable[P, Any]) -> Callable[[Callable[..., T]], Callable[P, T]]:
    """Decorator returning a cast of the original function"""

    def return_func(func: Callable[..., T]) -> Callable[P, T]:
        return cast(Callable[P, T], func)

    return return_func
