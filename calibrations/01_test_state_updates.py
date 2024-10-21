from qualibrate import NodeParameters, QualibrationNode, logger


class Parameters(NodeParameters):
    qubits: list[str] = ["q1", "q2", "q3"]

    str_value: str = "test"
    int_value: int = 1
    float_value: float = 1.0

    req_value: int


node = QualibrationNode("test_node", parameters=Parameters(req_value=1))

node.parameters.str_value

logger.info(f" ---- RUNNING NODE {node.name} BODY ---- ")


from random import randint

from quam import quam_dataclass
from quam.components import BasicQuAM, SingleChannel


@quam_dataclass
class CustomChannel(SingleChannel):
    intermediate_frequency: float = 100e6


machine = BasicQuAM(
    channels={
        "ch1": CustomChannel(opx_output=("con1", 1)),
        "ch2": CustomChannel(opx_output=("con1", 1)),
        "ch3": {
            "ch1": SingleChannel(
                opx_output=("con1", 1), intermediate_frequency=100e6
            )
        },
    },
)
channel = machine.channels["ch1"]

assert channel.intermediate_frequency == 100e6

with node.record_state_updates(interactive_only=False):
    channel.intermediate_frequency = 50e6
node.machine = machine

print("--------------Run node------------------")
# time.sleep(2)

if node.parameters and node.parameters.targets is not None:
    node.outcomes = {
        target: "successful" if bool(randint(0, 1)) else "failed"
        for target in node.parameters.targets
    }
node.results = {
    "str_val": node.parameters.str_value,
    "int_val": node.parameters.int_value,
    "float_val": node.parameters.float_value,
}
node.save()
