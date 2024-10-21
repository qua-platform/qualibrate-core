from time import sleep

import numpy as np
from matplotlib import pyplot as plt
from quam.components import *

from qualibrate import NodeParameters, QualibrationNode


class Parameters(NodeParameters):
    resonator: str = "q1.resonator"
    sampling_points: int = 100
    noise_factor: float = 0.1


node = QualibrationNode(
    name="test_node1",
    parameters=Parameters(),
    # description="Test calibration that wait a few seconds, then plots random data.",
)
# node.mode.interactive = True


machine = node.machine = BasicQuAM(
    channels={
        "ch1": SingleChannel(
            opx_output=("con1", 1), intermediate_frequency=100e6
        ),
        "ch2": SingleChannel(
            opx_output=("con1", 1), intermediate_frequency=[1, 2, 4]
        ),
    }
)

node.parameters = Parameters()

# Sleep for a few seconds to simulate the calibration
sleep(4)

fig, ax = plt.subplots()
xvals = np.linspace(-10, 10, node.parameters.sampling_points)
offset = np.random.rand() * 3
gaussian = np.exp(-((xvals + offset) ** 2))
noise = node.parameters.noise_factor * np.random.rand(
    node.parameters.sampling_points
)
ax.plot(xvals, gaussian + noise)
ax.set_xlabel("Frequency shift (Hz)")
ax.set_ylabel("Signal amplitude (a.u.)")

node.results = {"frequency_shift": offset, "results_fig": fig}

with node.record_state_updates():
    machine.channels["ch1"].intermediate_frequency = 50e6
    machine.channels["ch2"].intermediate_frequency = [1, 2, 3]

node.save()
