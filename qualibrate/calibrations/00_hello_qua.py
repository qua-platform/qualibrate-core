"""
A simple sandbox to showcase different QUA functionalities during the installation.
"""

from qualibrate import QualibrationNode, NodeParameters


class Parameters(NodeParameters):
    simulate: bool = False


node = QualibrationNode(
    name="hello_qua",
    parameters_class=NodeParameters,
)

node.parameters.simulate = True

###################################################
#  Load QuAM and open Communication with the QOP  #
###################################################

from qm.qua import *
from qm import SimulationConfig
from components import QuAM
from macros import node_save

# Instantiate the QuAM class from the state file
machine = QuAM.load("quam_state")
# Generate the OPX and Octave configurations
config = machine.generate_config()
octave_config = machine.get_octave_config()
# Open Communication with the QOP
qmm = machine.connect()


###################
# The QUA program #
###################
with program() as hello_qua:
    a = declare(fixed)
    with infinite_loop_():
        with for_(a, 0, a < 1.1, a + 0.05):
            play("x180" * amp(a), machine.qubits["q0"].xy.name)
        wait(25, machine.qubits["q0"].xy.name)
        align()
        measure("readout", machine.qubits["q1"].resonator.name, None)


###########################
# Run or Simulate Program #
###########################
if node.parameters.simulate:
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=1_000)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, hello_qua, simulation_config)
    # Plot the simulated samples
    job.get_simulated_samples().con1.plot()
else:
    # Open a quantum machine to execute the QUA program
    qm = qmm.open_qm(config)
    # Send the QUA program to the OPX, which compiles and executes it - Execute does not block python!
    job = qm.execute(hello_qua)
