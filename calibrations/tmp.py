from pathlib import Path

from qualibrate.qualibration_library import QualibrationLibrary

lib = QualibrationLibrary(
    Path(__file__).parent
)

node = lib.nodes["test_types"]
graph = lib.graphs["single_node_graph"]

# graph = lib.graphs["single_node_graph"]
#
#
# graph.run(qubits=["q2", "q3"])
