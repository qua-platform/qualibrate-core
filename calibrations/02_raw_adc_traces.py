"""
        RAW ADC TRACES
This script aims to measure data captured within a specific window defined by the measure() function.
We term the digitized, unprocessed data as "raw ADC traces" because they represent the acquired waveforms without any
real-time processing by the pulse processor, such as demodulation, integration, or time-tagging.

The script is useful for inspecting signals prior to demodulation, ensuring the ADCs are not saturated,
correcting any non-zero DC offsets, and estimating the SNR.
"""

from pydantic import BaseModel
from qualibrate import QualibrationNode, NodeParameters
from quam.components import InOutIQChannel


class Resonator(BaseModel):
    pass


class Parameters(NodeParameters):
    resonators: list = []
    simulate: bool = True


node = QualibrationNode(
    name="raw_adc_traces",
    parameters_class=Parameters,
)

# ###################################################
# #  Load QuAM and open Communication with the QOP  #
# ###################################################

# from qm.qua import *
# from qm import SimulationConfig
# import matplotlib.pyplot as plt
# import numpy as np
# from qualang_tools.units import unit
# from components import QuAM, Resonator
# from macros import node_save


# # Class containing tools to help handling units and conversions.
# u = unit(coerce_to_integer=True)
# # Instantiate the QuAM class from the state file
# machine = QuAM.load("quam_state")
# # Generate the OPX and Octave configurations
# config = machine.generate_config()
# octave_config = machine.get_octave_config()
# # Open Communication with the QOP
# qmm = machine.connect()

# # Get the relevant QuAM components
# rr1 = machine.active_qubits[0].resonator
# rr2 = machine.active_qubits[1].resonator
# rr = [q.resonator for q in machine.active_qubits]

# ###################
# # The QUA program #
# ###################
# n_avg = 100  # The number of averages

# with program() as raw_trace_prog:
#     n = declare(int)  # QUA variable for the averaging loop
#     adc_st = declare_stream(adc_trace=True)  # The stream to store the raw ADC trace

#     with for_(n, 0, n < n_avg, n + 1):  # QUA for_ loop for averaging
#         # Make sure that the readout pulse is sent with the same phase so that the acquired signal does not average out
#         reset_phase(rr1.name)
#         reset_phase(rr2.name)
#         # Measure the resonator (send a readout pulse and record the raw ADC trace)
#         rr1.measure("readout", stream=adc_st)
#         # Play the readout on rr2 as well for making sure that the ADC won't be saturated for multiplexed readout
#         rr2.measure("readout")
#         # Wait for the resonator to deplete
#         wait(machine.depletion_time * u.ns, rr1.name, rr2.name)

#     with stream_processing():
#         # Will save average:
#         adc_st.input1().average().save("adc1")
#         adc_st.input2().average().save("adc2")
#         # Will save only last run:
#         adc_st.input1().save("adc1_single_run")
#         adc_st.input2().save("adc2_single_run")


# ###########################
# # Run or Simulate Program #
# ###########################

# if node.parameters.simulate:
#     # Simulates the QUA program for the specified duration
#     simulation_config = SimulationConfig(duration=10_000)  # In clock cycles = 4ns
#     # Simulate blocks python until the simulation is done
#     job = qmm.simulate(config, raw_trace_prog, simulation_config)
#     # Plot the simulated samples
#     job.get_simulated_samples().con1.plot()

# else:
#     # Open a quantum machine to execute the QUA program
#     qm = qmm.open_qm(config)
#     # Send the QUA program to the OPX, which compiles and executes it
#     job = qm.execute(raw_trace_prog)
#     # Creates a result handle to fetch data from the OPX
#     res_handles = job.result_handles
#     # Waits (blocks the Python console) until all results have been acquired
#     res_handles.wait_for_all_values()
#     # Fetch the raw ADC traces and convert them into Volts
#     adc1 = u.raw2volts(res_handles.get("adc1").fetch_all())
#     adc2 = u.raw2volts(res_handles.get("adc2").fetch_all())
#     adc1_single_run = u.raw2volts(res_handles.get("adc1_single_run").fetch_all())
#     adc2_single_run = u.raw2volts(res_handles.get("adc2_single_run").fetch_all())
#     # Plot data
#     fig = plt.figure()
#     plt.subplot(121)
#     plt.title("Single run")
#     plt.plot(adc1_single_run, label="Input 1")
#     plt.plot(adc2_single_run, label="Input 2")
#     plt.xlabel("Time [ns]")
#     plt.ylabel("Signal amplitude [V]")
#     plt.legend()

#     plt.subplot(122)
#     plt.title("Averaged run")
#     plt.plot(adc1, label="Input 1")
#     plt.plot(adc2, label="Input 2")
#     plt.xlabel("Time [ns]")
#     plt.legend()
#     plt.tight_layout()

#     print(f"\nInput1 mean: {np.mean(adc1)} V\n" f"Input2 mean: {np.mean(adc2)} V")

#     # Update QUAM
#     rr1.opx_input_offset_I -= np.mean(adc1)
#     rr2.opx_input_offset_I -= np.mean(adc1)
#     rr1.opx_input_offset_Q -= np.mean(adc2)
#     rr2.opx_input_offset_Q -= np.mean(adc2)

#     # Save data from the node
#     data = {
#         "offset_1": np.mean(adc1),
#         "offset_2": np.mean(adc2),
#         "raw_adc_1": adc1,
#         "raw_adc_2": adc2,
#         "raw_adc_1_single_shot": adc1_single_run,
#         "raw_adc_2_single_shot": adc2_single_run,
#         "figure": fig,
#     }
#     node_save("raw_adc_traces", data, machine)
