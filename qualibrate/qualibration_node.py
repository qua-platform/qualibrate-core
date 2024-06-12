from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping, Type, Optional

from qualibrate import NodeParameters
from qualibrate.storage import StorageManager


class StopInspection(Exception):
    pass


class QualibrationNode:
    mode: str = "default"
    storage_manager: Optional[StorageManager] = None
    last_instantiated_node: Optional["QualibrationNode"] = None

    def __init__(self, name, parameters_class: Type[NodeParameters], description=None):
        self.name = name
        self.parameters_class = parameters_class
        self.description = description

        self.parameters: Optional[NodeParameters] = None
        self._state_updates = {}
        self.results = {}
        self.node_filepath: Optional[Path] = None

        if self.mode == "inspection":
            self.last_instantiated_node = self
            raise StopInspection("Node instantiated in inspection mode")

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

    def save(self):
        self.storage_manager.save(node=self)

    def run_node(self, input_parameters):
        if QualibrationNode.mode != "external":
            raise RuntimeError(
                f"Node can only be run in external mode, not in mode: {QualibrationNode.mode}"
            )
        self.run_node_file(self.node_filepath)

    def run_node_file(self, node_filepath):  # TODO
        raise NotImplementedError

    def _record_state_update(self, attr, val):
        self._state_updates[attr] = val

    @contextmanager
    def record_state_updates(self):
        if self.mode == "interactive":
            # Override QuamComponent.__setattr__()
            try:
                from quam.core import QuamBase

                setattr_func = QuamBase.__setattr__
                QuamBase.__setattr__ = self._record_state_update()
                yield
            finally:
                QuamBase.__setattr__ = setattr_func
        else:
            yield
