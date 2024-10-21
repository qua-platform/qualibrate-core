from qualibrate import NodeParameters, QualibrationNode


class Parameters(NodeParameters):
    pass


node = QualibrationNode("check_latest_node", parameters=Parameters())
