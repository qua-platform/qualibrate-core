from contextlib import contextmanager
from typing import Type, Mapping, Any

from qualibrate.storage import StorageManager
from qualibrate import NodeParameters


class QualibrationNode:
    mode: str = "default"
    storage_manager: StorageManager = None

    def __init__(self, name, parameters_class: Type[NodeParameters], description=None):
        self.name = name
        self.parameters_class = parameters_class
        self.description = description

        self.parameters: Type[NodeParameters] = parameters_class
        self._state_updates = {}

        if self.mode == "library_scan":
            from qualibrate.qualibration_library import (
                QualibrationLibrary,
                LibraryScanException,
            )

            QualibrationLibrary.active_library.add_node(self)
            raise LibraryScanException(
                "Scanning library, aborting further script execution"
            )

    def serialize(self) -> Mapping[str, Any]:
        return {
            "name": self.name,
            "parameters": self.parameters.serialize(),
            "description": self.description,
        }

    def save(self): ...

    def _record_state_update(self, attr, val):
        self._state_updates[attr] = val

    @contextmanager
    def record_state_updates(self):
        if self.mode == "interactive":
            # Override QuamComponent.__setattr__()
            try:
                from quam.core import QuamBase

                setattr_func = QuamBase.__setattr__
                QuamBase.__setattr__ = self._record_setattr()
                yield
            finally:
                QuamBase.__setattr__ = setattr_func
        else:
            yield
