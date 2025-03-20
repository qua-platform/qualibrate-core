from _collections_abc import dict_items, dict_values
from collections.abc import ItemsView, ValuesView
from copy import copy
from typing import Optional, TypeVar, Union, cast, overload

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class RunnableCollection(dict[_KT, _VT]):
    def __getitem__(self, key: _KT) -> _VT:
        return copy(super().__getitem__(key))

    @overload
    def get(self, key: _KT) -> Optional[_VT]: ...

    @overload
    def get(self, key: _KT, default: _T) -> Union[_VT, _T]: ...

    def get(
        self, key: _KT, default: Union[_T, None] = None
    ) -> Union[_VT, _T, None]:
        if key in self:
            return copy(super().get(key))
        return default

    def get_nocopy(
        self, key: _KT, /, default: Union[_T, None] = None
    ) -> Union[_T, _VT, None]:
        return super().get(key, default)

    def items(self) -> "dict_items[_KT, _VT]":
        return cast(
            "dict_items[_KT, _VT]",
            ItemsView({k: copy(v) for k, v in super().items()}),
        )

    def items_nocopy(self) -> "dict_items[_KT, _VT]":
        return super().items()

    def values(self) -> "dict_values[_KT, _VT]":
        return cast(
            "dict_values[_KT, _VT]",
            ValuesView({k: copy(v) for k, v in super().items()}),
        )

    def values_nocopy(self) -> "dict_values[_KT, _VT]":
        return super().values()
