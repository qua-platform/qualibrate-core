"""
        RESONATOR SPECTROSCOPY
This sequence involves measuring the resonator by sending a readout pulse and demodulating the signals to extract the
'I' and 'Q' quadratures across varying readout intermediate frequencies.
The data is then post-processed to determine the resonator resonance frequency.
This frequency can be used to update the readout frequency in the state.

Prerequisites:
    - Ensure calibration of the time of flight, offsets, and gains (referenced as "time_of_flight").
    - Calibrate the IQ mixer connected to the readout line (whether it's an external mixer or an Octave port).
    - Define the readout pulse amplitude and duration in the configuration.
    - Specify the expected resonator depletion time in the configuration.

Before proceeding to the next node:
    - Update the readout frequency, labeled as f_res and f_opt, in the state.
    - Save the current state by calling machine.save("quam")
"""

from typing import Optional
from qualibrate import QualibrationNode, NodeParameters


class Parameters(NodeParameters):
    resonator: Optional[str] = None
    n_avg: int = 100
    simulate: bool = True
    f_min: float = 10e6
    f_max = 251e6
    f_step = 1e6


node = QualibrationNode(
    name="resonator_spectroscopy_single",
    parameters_class=Parameters,
)

# Specify parameters used when running this script locally
node.parameters = Parameters(resonator="#/qubits/q0/resonator", simulate=True)


from qm.qua import *
from qm import SimulationConfig
from qualang_tools.results import progress_counter, fetching_tool
from qualang_tools.plot import interrupt_on_close
from qualang_tools.loops import from_array
from qualang_tools.units import unit
from components import QuAM
from macros import node_save
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


###################################################
#  Load QuAM and open Communication with the QOP  #
###################################################
# Class containing tools to help handling units and conversions.
u = unit(coerce_to_integer=True)
# Instantiate the QuAM class from the state file
machine = QuAM.load("quam_state")
node.machine = machine
# Generate the OPX and Octave configurations
config = machine.generate_config()
octave_config = machine.get_octave_config()
# Open Communication with the QOP
qmm = machine.connect()

# Get the relevant QuAM components
rr = machine._get_reference(node.parameters.resonator)  # The resonator to measure

###################
# The QUA program #
###################
# The frequency sweep parameters
## rr1
# frequencies = np.arange(10e6, 251e6, 1e6)
# rr2
frequencies = np.arange(
    node.parameters.f_min, node.parameters.f_max, node.parameters.f_step
)

with program() as resonator_spec:
    n = declare(int)  # QUA variable for the averaging loop
    f = declare(int)  # QUA variable for the readout frequency
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'

    # Bring the active qubits to the minimum frequency point
    machine.apply_all_flux_to_min()

    with for_(n, 0, n < node.parameters.n_avg, n + 1):  # QUA for_ loop for averaging
        with for_(
            *from_array(f, frequencies)
        ):  # QUA for_ loop for sweeping the frequency
            # Update the frequency of the digital oscillator linked to the resonator element
            update_frequency(rr.name, f)
            # Measure the resonator (send a readout pulse and demodulate the signals to get the 'I' & 'Q' quadratures)
            rr.measure("readout", qua_vars=(I, Q))
            # Wait for the resonator to deplete
            rr.wait(machine.depletion_time * u.ns)
            # Save the 'I' & 'Q' quadratures to their respective streams
            save(I, I_st)
            save(Q, Q_st)
            # Save the averaging iteration to get the progress bar
        save(n, n_st)

    with stream_processing():
        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
        I_st.buffer(len(frequencies)).average().save("I")
        Q_st.buffer(len(frequencies)).average().save("Q")
        n_st.save("iteration")


#######################
# Simulate or execute #
#######################
if node.parameters.simulate:
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=10_000)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, resonator_spec, simulation_config)
    # Plot the simulated samples
    job.get_simulated_samples().con1.plot()

else:
    # Open the quantum machine
    qm = qmm.open_qm(config)
    # Calibrate the active qubits
    # machine.calibrate_octave_ports(qm)
    # Send the QUA program to the OPX, which compiles and executes it
    job = qm.execute(resonator_spec)
    # Get results from QUA program
    node.results = fetching_tool(job, data_list=["I", "Q", "iteration"], mode="live")
    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    while node.results.is_processing():
        # Fetch results
        I, Q, iteration = node.results.fetch_all()
        # Convert results into Volts
        S = u.demod2volts(I + 1j * Q, rr.operations["readout"].length)
        R = np.abs(S)  # Amplitude
        phase = np.angle(S)  # Phase
        # Progress bar
        progress_counter(
            iteration, node.parameters.n_avg, start_time=node.results.get_start_time()
        )
        # Plot results
        plt.suptitle(
            f"{rr.name} spectroscopy - LO = {rr.frequency_converter_up.LO_frequency / u.GHz} GHz"
        )
        ax1 = plt.subplot(211)
        plt.cla()
        plt.plot(frequencies / u.MHz, R, ".")
        plt.ylabel(r"$R=\sqrt{I^2 + Q^2}$ [V]")
        plt.subplot(212, sharex=ax1)
        plt.cla()
        plt.plot(frequencies / u.MHz, signal.detrend(np.unwrap(phase)), ".")
        plt.xlabel("Intermediate frequency [MHz]")
        plt.ylabel("Phase [rad]")
        plt.pause(0.1)
        plt.tight_layout()

    # Close the quantum machines at the end in order to put all flux biases to 0 so that the fridge doesn't heat-up
    qm.close()

    # Save data from the node
    node.results = {
        "frequencies": frequencies,
        "R": R,
        "phase": signal.detrend(np.unwrap(phase)),
        "figure_raw": fig,
    }

    # Fit the results to extract the resonance frequency
    try:
        from qualang_tools.plot.fitting import Fit

        fit = Fit()
        fig_fit = plt.figure()
        res_spec_fit = fit.reflection_resonator_spectroscopy(
            frequencies / u.MHz, R, plot=True
        )
        plt.title(
            f"{rr.name} spectroscopy - LO = {rr.frequency_converter_up.LO_frequency / u.GHz} GHz"
        )
        plt.xlabel("Intermediate frequency [MHz]")
        plt.ylabel(r"R=$\sqrt{I^2 + Q^2}$ [V]")
        print(
            f"Resonator resonance frequency to update in the config: resonator_IF = {res_spec_fit['f'][0]:.6f} MHz"
        )

        # Update QUAM
        rr.intermediate_frequency = int(res_spec_fit["f"][0] * u.MHz)
        rr.frequency_bare = rr.rf_frequency
        # Save data from the node
        node.results[f"{rr.name}"] = {
            "resonator_frequency": int(res_spec_fit["f"][0] * u.MHz),
            "successful_fit": True,
        }
        node.results["figure_fit"] = fig_fit

    except (Exception,):
        node.results["successful_fit"] = False
        pass

    # Save data from the node
    node.save()
