from pydantic import Field

from qualibrate import QualibrationNode, NodeParameters


class Parameters(NodeParameters):
    qubits: list[str] = Field(default_factory=list)

    sampling_points: int = 100


node = QualibrationNode(
    name="forth_node",
    parameters=Parameters(),
    description="Description.",
)

raise ValueError("Execution error")
