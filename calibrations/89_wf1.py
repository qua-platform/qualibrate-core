from typing import List

from qualibrate import logger
from qualibrate.orchestration.basic_orchestrator import BasicOrchestrator
from qualibrate.parameters import GraphParameters
from qualibrate.qualibration_graph import QualibrationGraph
from qualibrate.qualibration_library import QualibrationLibrary

library = QualibrationLibrary.get_active_library()


class Parameters(GraphParameters):
    qubits: List[str]


node1 = library.nodes["wf_node1"].copy(sampling_points=500)
node2 = library.nodes["wf_node2"]
node3 = library.nodes["wf_node2"].copy(name="wf_node3")


nodes = {
    "wf_node1": node1,
    "wf_node2": node2,
    "wf_node3": node3,
}

g = QualibrationGraph(
    name="workflow1",
    parameters=Parameters(qubits=["q1", "q2", "q5"]),
    nodes=nodes,
    connectivity=[("wf_node1", "wf_node2")],
    orchestrator=BasicOrchestrator(skip_failed=True),
)

logger.info(f" ---- RUNNING GRAPH {g.name} BODY ---- ")

# print(g._nodes)
res = g.run(qubits=["q0", "q1", "q2"])
print(res)
print(g._orchestrator._execution_history)
