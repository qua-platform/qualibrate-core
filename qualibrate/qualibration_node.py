import warnings
from contextlib import contextmanager
from enum import Enum
from functools import partialmethod
from importlib.util import find_spec
from pathlib import Path
from types import MappingProxyType
from typing import Any, Generator, Mapping, Optional, Type

from qualibrate import NodeParameters
from qualibrate.storage import StorageManager
from qualibrate.storage.local_storage_manager import LocalStorageManager


class StopInspection(Exception):
    pass


class NodeMode(Enum):
    default = "default"
    inspection = "inspection"
    external = "external"
    interactive = "interactive"


class QualibrationNode:
    mode: NodeMode = NodeMode.default
    storage_manager: Optional[StorageManager] = None
    last_instantiated_node: Optional["QualibrationNode"] = None

    _singleton_instance = None  # configurable Singleton features

    # Singleton control
    def __new__(cls, *args: Any, **kwargs: Any) -> "QualibrationNode":
        if cls._singleton_instance is None:
            return super(QualibrationNode, cls).__new__(cls)
        return cls._singleton_instance

    def __init__(
        self,
        name: str,
        parameters_class: Type[NodeParameters],
        description: Optional[str] = None,
    ):
        if hasattr(self, "_initialized"):
            return

        self.name = name
        self.parameters_class = parameters_class
        self.description = description

        self.__parameters: Optional[NodeParameters] = None
        self._state_updates: dict[str, Any] = {}
        self.results: dict[Any, Any] = {}
        self.node_filepath: Optional[Path] = None
        self.machine = None

        self._initialized = True

        if self.mode == NodeMode.inspection:
            # ASK: Looks like `last_instantiated_node` and
            #  `_singleton_instance` have same logic -- keep instance of class
            #  in class-level variable. Is it needed to have both?
            self.__class__.last_instantiated_node = self
            raise StopInspection("Node instantiated in inspection mode")

    @property
    def parameters(self) -> Optional[NodeParameters]:
        return self.__parameters

    @parameters.setter
    def parameters(self, new_parameters: NodeParameters) -> None:
        if self.mode == NodeMode.external and self.__parameters is not None:
            return
        if not isinstance(new_parameters, self.parameters_class):
            raise TypeError(
                "Expected parameters is instance of "
                f"{self.parameters_class.__module__}"
                f".{self.parameters_class.__name__}"
            )
        self.__parameters = new_parameters

    @property
    def snapshot_idx(self) -> Optional[int]:
        if self.storage_manager is None:
            return None
        return self.storage_manager.snapshot_idx

    def serialize(self) -> Mapping[str, Any]:
        return {
            "name": self.name,
            "input_parameters": self.parameters_class.serialize(),
            "description": self.description,
        }

    def save(self) -> None:
        if self.storage_manager is None:
            # TODO: fully depend on qualibrate. Need to remove this dependency.
            warnings.warn(
                "Node.storage_manager should be defined to save node, "
                "resorting to default configuration"
            )
            from qualibrate_app.config import get_config_path, get_settings

            config_path = get_config_path()
            settings = get_settings(config_path)
            self.storage_manager = LocalStorageManager(
                root_data_folder=settings.user_storage
            )
        self.storage_manager.save(node=self)

    def run_node(self, input_parameters: NodeParameters) -> None:
        mode = self.mode
        try:
            self.mode = NodeMode.external
            self.__parameters = input_parameters
            # TODO: raise exception if node file isn't specified
            self.run_node_file(self.node_filepath)
        finally:
            self.mode = mode

    def run_node_file(self, node_filepath: Optional[Path]) -> None:
        try:
            # Temporarily set the singleton instance to this node
            self.__class__._singleton_instance = self
            code = node_filepath.read_text()  # type: ignore[union-attr]
            exec(code)
        finally:
            self.__class__._singleton_instance = None

    @property
    def state_updates(self) -> MappingProxyType[str, Any]:
        return MappingProxyType(self._state_updates)

    @contextmanager
    def record_state_updates(
        self, interactive_only=True
    ) -> Generator[None, None, None]:
        if self.mode != NodeMode.interactive and interactive_only:
            yield
            return

        quam_core_spec = find_spec("core", "quam")
        # quam not installed
        if quam_core_spec is None:
            yield
            return

        # Override QuamComponent.__setattr__()
        from quam.core import (
            QuamBase,
            QuamComponent,
            QuamDict,
            QuamList,
            QuamRoot,
        )

        quam_classes_mapping = (
            QuamBase,
            QuamComponent,
            QuamRoot,
            QuamDict,
        )
        quam_classes_sequences = (QuamList, QuamDict)

        cls_setattr_funcs = {
            cls: cls.__dict__["__setattr__"]
            for cls in quam_classes_mapping
            if "__setattr__" in cls.__dict__
        }
        cls_setitem_funcs = {
            cls: cls.__dict__["__setitem__"]
            for cls in quam_classes_sequences
            if "__setitem__" in cls.__dict__
        }
        try:
            for cls in cls_setattr_funcs:
                setattr(
                    cls,
                    "__setattr__",
                    partialmethod(_record_state_update_getattr, node=self),
                )
            for cls in cls_setitem_funcs:
                setattr(
                    cls,
                    "__setitem__",
                    partialmethod(_record_state_update_getitem, node=self),
                )
            yield
        finally:
            for cls, setattr_func in cls_setattr_funcs.items():
                setattr(cls, "__setattr__", setattr_func)
            for cls, setitem_func in cls_setitem_funcs.items():
                setattr(cls, "__setitem__", setitem_func)


def _record_state_update_getattr(
    quam_obj,
    attr: str,
    val: Any = None,
    node=None,
) -> None:
    reference = quam_obj.get_reference(attr)
    old = getattr(quam_obj, attr)
    if node:
        node._state_updates[reference] = {
            "key": reference,
            "attr": attr,
            "old": old,
            "val": val,
        }


def _record_state_update_getitem(
    quam_obj,
    attr: str,
    val: Any = None,
    node=None,
) -> None:
    reference = quam_obj.get_reference(attr)
    old = quam_obj[attr]
    if node:
        node._state_updates[reference] = {
            "key": reference,
            "attr": attr,
            "old": old,
            "val": val,
        }
