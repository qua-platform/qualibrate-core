from qualibrate import QualibrationNode, NodeParameters
from quam.components import *


class Parameters(NodeParameters):
    resonator: str = "hi"
    simulate: bool = True


node = QualibrationNode(
    name="test_cal",
    parameters_class=Parameters,
)
# node.mode.interactive = True

node.machine = BasicQuAM(
    channels={
        "ch1": SingleChannel(opx_output=("con1", 1), intermediate_frequency=100e6)
    }
)

node.parameters = Parameters()

# Temporarily sleep 8 seconds
from time import sleep

sleep(4)

node.results = {
    "resonator_val": node.parameters.resonator,
    "simulate": node.parameters.simulate,
}

with node.record_state_updates():
    channel = node.machine.channels["ch1"]
    channel.intermediate_frequency = 50e6

node.save()
