from dataclasses import field

from qualibrate import NodeParameters, QualibrationNode


class Parameters(NodeParameters):
    qubits: list[str] = ["a", "b"]

    # str_value: str = "test"
    int_value: int = 4
    # float_value: float = 1.0
    bool_value: bool = False

    list_str: list[str] = ["a", "b"]
    # list_int: list[int] = [1, 2]
    # list_float: list[float] = [1.1, 2.2]
    # list_bool: list[bool] = [True, False]


node = QualibrationNode("test_types", parameters=Parameters())

from quam import quam_dataclass
from quam.components import BasicQuAM, SingleChannel


@quam_dataclass
class CustomChannel(SingleChannel):
    state_update_str: str
    state_update_int: int
    state_update_float: float
    state_update_bool: bool
    state_update_list_str: list[str] = field(
        default_factory=node.parameters.list_str
    )
    state_update_list_int: list[int] = field(
        default_factory=node.parameters.list_int
    )
    state_update_list_float: list[float] = field(
        default_factory=node.parameters.list_float
    )
    state_update_list_bool: list[bool] = field(
        default_factory=node.parameters.list_bool
    )


machine = BasicQuAM(
    channels={
        "ch1": CustomChannel(
            opx_output=("con1", 1),
            state_update_str=node.parameters.str_value,
            state_update_int=node.parameters.int_value,
            state_update_float=node.parameters.float_value,
            state_update_bool=node.parameters.bool_value,
            state_update_list_str=node.parameters.list_str,
            state_update_list_int=node.parameters.list_int,
            state_update_list_float=node.parameters.list_float,
            state_update_list_bool=node.parameters.list_bool,
        )
    },
)
channel = machine.channels["ch1"]

with node.record_state_updates():
    channel.state_update_str = channel.state_update_str + "_add"
    channel.state_update_int = channel.state_update_int + 3
    channel.state_update_float = channel.state_update_float / 10
    channel.state_update_bool = not channel.state_update_bool
    channel.state_update_list_str = [
        f"_{i}_" for i in channel.state_update_list_str
    ]
    channel.state_update_list_int = [
        i - 3 for i in channel.state_update_list_int
    ]
    channel.state_update_list_float = [
        round(i / 3, 3) for i in channel.state_update_list_float
    ]
    channel.state_update_list_bool = [
        not i for i in channel.state_update_list_bool
    ]


node.machine = machine
node.save()
