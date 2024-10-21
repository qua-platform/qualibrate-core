from qualibrate import NodeParameters, QualibrationNode


class Parameters(NodeParameters):
    qubits: list[str] = []


node = QualibrationNode(
    name="test_import",
    parameters=Parameters(),
)
node.parameters = Parameters()


#
# import requests
#
#
# class Check:
#     def call(self):
#         print(f"inside function {locals() = }")
#         return requests.get("https://ya.ru").content.decode()
#
#
# check = Check()
# r = check.call()
# print(r)
