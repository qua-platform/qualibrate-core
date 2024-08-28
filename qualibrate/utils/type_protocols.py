from typing import Any, Hashable, Optional, Protocol

TargetType = Hashable


class GetRefProtocol(Protocol):
    def get_reference(self, attr: Optional[str]) -> str: ...


class GetRefGetItemProtocol(GetRefProtocol, Protocol):
    def __getitem__(self, attr: Optional[str]) -> Any:
        pass
