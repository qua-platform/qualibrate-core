from typing import List

from qualibrate.orchestration.basic_orchestrator import BasicOrchestrator
from qualibrate.parameters import GraphParameters
from qualibrate.qualibration_graph import QualibrationGraph
from qualibrate.qualibration_library import QualibrationLibrary

library = QualibrationLibrary.get_active_library()

nodes = {
    "test_node": library.nodes["test_node"],
    "one_more_node": library.nodes["one_more_node"],
}


class GraphParams(GraphParameters):
    qubits: List[str] = []

    str_value: str = "test"
    int_value: int = 1
    float_value: float = 1.0


graph = QualibrationGraph(
    "test_orch",
    GraphParams(),
    nodes,
    (("test_node", "one_more_node"),),
    orchestrator=BasicOrchestrator(),
)

if __name__ == "__main__":
    result = graph.run(
        targets=["q1", "a1", "b1"],
        nodes={"test_node": {"req_value": 1}, "one_more_node": {}},
    )
    print(result)
