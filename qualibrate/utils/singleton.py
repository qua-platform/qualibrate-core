from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Singleton(type, Generic[T]):
    _instances: dict[Singleton[T], T] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> T:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
