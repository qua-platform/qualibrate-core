from qualibrate.orchestration.basic_orchestrator import BasicOrchestrator
from qualibrate.parameters import GraphParameters
from qualibrate.qualibration_graph import QualibrationGraph
from qualibrate.qualibration_library import QualibrationLibrary

library = QualibrationLibrary.get_active_library()

one_more_node = library.nodes["one_more_node"]
node_copy = one_more_node.copy("one_more_node_copy", str_value="aaa")

nodes = {
    **library.nodes,
    "one_more_node_copy": node_copy,
}


class GraphParams(GraphParameters):
    qubits: list[str] = []

    str_value: str = "test"
    int_value: int = 1
    float_value: float = 1.0


graph = QualibrationGraph(
    "test_graph",
    GraphParams(),
    nodes,
    (
        ("test_node", "one_more_node"),
        ("one_more_node", "test_cal"),
        ("test_cal", "one_more_node_copy"),
    ),
    orchestrator=BasicOrchestrator(),
)

if __name__ == "__main__":
    graph_results = library.run_graph(
        "test_graph",
        graph.full_parameters_class(
            parameters={"targets": ["q1", "q2"]},
            nodes={
                "test_node": {"req_value": 1},
                "test_cal": {},
                "one_more_node": {},
                "one_more_node_copy": {},
            },
        ),
    )
    # graph_results = graph.run(
    #     targets=["q1", "q2"],
    #     nodes={
    #         "test_node": {"req_value": 11},
    #         "one_more_node": {},
    #         "test_cal": {},
    #         "one_more_node_copy": {}
    #     }
    # )
    print(graph_results)
