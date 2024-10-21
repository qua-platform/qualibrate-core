from typing import ClassVar, Optional

from qualibrate.orchestration.basic_orchestrator import BasicOrchestrator
from qualibrate.parameters import GraphParameters
from qualibrate.qualibration_graph import QualibrationGraph
from qualibrate.qualibration_library import QualibrationLibrary

library = QualibrationLibrary.get_active_library()

nodes = {"test_types": library.nodes["test_types"]}


class GraphParams(GraphParameters):
    targets_name: ClassVar[Optional[str]] = "qubits_"
    qubits_: list[str] = []

    str_value: str = "test"
    int_value: int = 1
    float_value: float = 1.0


graph = QualibrationGraph(
    "single_node_graph",
    GraphParams(),
    nodes,
    tuple(),
    orchestrator=BasicOrchestrator(),
)
