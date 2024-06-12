from qualibrate import QualibrationNode, NodeParameters


class Parameters(NodeParameters):
    resonator: str = "hi"
    simulate: bool = True


node = QualibrationNode(
    name="test_cal",
    parameters_class=Parameters,
)

node.parameters = Parameters()

# Temporarily sleep 8 seconds
from time import sleep

sleep(4)

node.results = {"value1": 42}
node.machine = {
    "qubits": {
        "q0": {
            "id": 0,
            "xy": {
                "opx_output_I": "#/wiring/qubits/0/port_I",
                "opx_output_Q": "#/wiring/qubits/0/port_Q",
                "frequency_converter_up": "#/octave/RF_outputs/2",
                "intermediate_frequency": -103658560.7967306,
            },
        }
    }
}

node.save()
