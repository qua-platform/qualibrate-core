from typing import Optional

import pytest
from pydantic import ValidationError

from qualibrate.parameters import GraphParameters, NodeParameters


class TestCreateParameters:
    class SampleNodeParameters(NodeParameters):
        qubits: Optional[list[str]] = None
        other_param: str = "test"

    class SampleGraphParameters(GraphParameters):
        qubits: Optional[list[str]] = None
        other_param: str = "test"

    @pytest.mark.parametrize(
        "parameters_class", [SampleNodeParameters, SampleGraphParameters]
    )
    def test_forbid_extra_parameters(self, parameters_class):
        with pytest.raises(ValidationError) as ex:
            parameters_class.model_validate({"invalid_key": None})
        errors = ex.value.errors()
        assert errors[0]["type"] == "extra_forbidden"
        assert errors[0]["loc"] == ("invalid_key",)

    def test_node_targets_name(self):
        assert NodeParameters.targets_name == "qubits"

    def test_graph_targets_name(self):
        assert GraphParameters.targets_name == "qubits"

    @pytest.mark.parametrize(
        "parameters_class", [SampleNodeParameters, SampleGraphParameters]
    )
    def test_serialize_include_targets(self, parameters_class):
        assert parameters_class.serialize(exclude_targets=False) == {
            "qubits": {
                "anyOf": [
                    {"items": {"type": "string"}, "type": "array"},
                    {"type": "null"},
                ],
                "default": None,
                "title": "Qubits",
                "is_targets": True,
            },
            "other_param": {
                "default": "test",
                "title": "Other Param",
                "type": "string",
                "is_targets": False,
            },
        }

    @pytest.mark.parametrize(
        "parameters_class", [SampleNodeParameters, SampleGraphParameters]
    )
    def test_serialize_exclude_targets(self, parameters_class):
        assert parameters_class.serialize(exclude_targets=True) == {
            "other_param": {
                "default": "test",
                "title": "Other Param",
                "type": "string",
                "is_targets": False,
            }
        }

    @pytest.mark.parametrize(
        "parameters_class", [SampleNodeParameters, SampleGraphParameters]
    )
    def test_serialize_no_exclude_param(self, parameters_class):
        assert parameters_class.serialize() == {
            "qubits": {
                "anyOf": [
                    {"items": {"type": "string"}, "type": "array"},
                    {"type": "null"},
                ],
                "default": None,
                "title": "Qubits",
                "is_targets": True,
            },
            "other_param": {
                "default": "test",
                "title": "Other Param",
                "type": "string",
                "is_targets": False,
            },
        }
