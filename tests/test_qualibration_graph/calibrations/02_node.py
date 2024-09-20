from qualibrate import NodeParameters, QualibrationNode


class Parameters(NodeParameters):
    qubits: list[str] = []

    str_value: str = "test"
    float_value: float = 1.0


node = QualibrationNode("one_more_node", parameters=Parameters())
node.parameters = Parameters()

import requests

response = requests.get("https://ya.ru")
assert response.status_code == 200

