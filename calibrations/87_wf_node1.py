from pydantic import Field

from qualibrate import NodeParameters, QualibrationNode, logger


class Parameters(NodeParameters):
    qubits: list[str] = Field(default_factory=list)

    sampling_points: int = 100
    noise_factor: float = 0.1


node = QualibrationNode(
    name="wf_node1",
    parameters=Parameters(),
)

from time import sleep

import numpy as np
from quam import quam_dataclass
from quam.components import BasicQuAM, SingleChannel

logger.info(f" ---- RUNNING NODE {node.name} BODY ---- ")


@quam_dataclass
class CustomChannel(SingleChannel):
    intermediate_frequency: float = 100e6


machine = BasicQuAM(
    channels={
        "ch1": CustomChannel(opx_output=("con1", 1)),
        "ch2": CustomChannel(opx_output=("con1", 2)),
        "ch3": {
            "ch1": SingleChannel(
                opx_output=("con1", 1), intermediate_frequency=100e6
            )
        },
    },
)

node.machine = machine

sleep(5)

node.results = node.parameters.model_dump()
if node.parameters.targets is not None:
    node.outcomes = {
        t: "successful" if np.random.rand() > 0.5 else "failed"
        for t in node.parameters.targets
    }

node.save()
