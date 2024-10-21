from qualibrate import NodeParameters, QualibrationNode


class Parameters(NodeParameters):
    qubits: list[str] = ["q1", "q2"]

    str_value: str = "test"
    float_value: float = 1.0


node = QualibrationNode("one_more_node", parameters=Parameters())
node.parameters = Parameters(float_value=1.2)



from random import randint

import requests


class P:
    def f(self):
        response = requests.get("https://ya.ru")
        print(response.status_code)


raise ValueError("Check msg")

P().f()
if node.parameters and node.parameters.targets is not None:
    node.outcomes = {
        target: ("successful" if bool(randint(0, 1)) else "failed")
        for target in node.parameters.targets
    }
