import importlib
import sys
from enum import Enum
from pathlib import Path
from queue import Queue
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

import networkx as nx
from pydantic import create_model

from qualibrate.parameters import (
    ExecutionParameters,
    GraphParameters,
    NodesParameters,
)
from qualibrate.q_runnnable import QRunnable, file_is_calibration_instance
from qualibrate.qualibration_node import QualibrationNode
from qualibrate.storage.local_storage_manager import logger
from qualibrate.utils.exceptions import StopInspection

if TYPE_CHECKING:
    from qualibrate import QualibrationLibrary


__all__ = ["NodeState", "QGraphBaseType", "QualibrationGraph"]


class NodeState(Enum):
    pending: str = "pending"
    running: str = "running"
    successful: str = "successful"
    failed: str = "failed"


QGraphBaseType = QRunnable[GraphParameters]


class QualibrationGraph(QRunnable[GraphParameters]):
    _node_init_args = {"state": NodeState.pending, "retries": 0}
    last_instantiated_graph: Optional["QualibrationGraph"] = None

    def __init__(
        self,
        name: str,
        parameters_class: Type[GraphParameters],
        adjacency: Mapping[str, Sequence[str]],
    ):
        """
        :param name: graph name
        :param parameters_class: class of parameters
        :param adjacency: Adjacency list.
            Format: `{"name_1": ["name_2", "name_3"], "name_2": ["name_3"]}`
        """
        super().__init__(name, parameters_class)
        self._adjacency = adjacency
        self.full_parameters: Optional[Type[ExecutionParameters]] = None
        self._graph = nx.DiGraph()

        qlib = self._get_qlibrary_or_error()
        for v_name, xs_names in adjacency.items():
            v = self._add_node_by_name(v_name, qlib)
            for x_name in xs_names:
                x = self._add_node_by_name(x_name, qlib)
                self._graph.add_edge(v, x)
        self._build_parameters_class()

        if self.mode.inspection:
            # ASK: Looks like `last_instantiated_node` and
            #  `_singleton_instance` have same logic -- keep instance of class
            #  in class-level variable. Is it needed to have both?
            self.__class__.last_instantiated_graph = self
            raise StopInspection("Node instantiated in inspection mode")

    # TODO: logic commonly same with node so need to move to
    @classmethod
    def scan_folder_for_instances(
        cls, path: Path, library: "QualibrationLibrary"
    ) -> Dict[str, QGraphBaseType]:
        graphs: Dict[str, QGraphBaseType] = {}
        inspection = cls.mode.inspection
        str_path = str(path)
        lib_path_exists = str_path in sys.path
        if not lib_path_exists:
            sys.path.append(str_path)
        try:
            cls.mode.inspection = True

            for file in sorted(path.iterdir()):
                if not file_is_calibration_instance(file, cls.__name__):
                    continue
                cls.scan_graph_file(file, graphs)
        finally:
            if not lib_path_exists:
                sys.path.remove(str_path)
            cls.mode.inspection = inspection
        return graphs

    @classmethod
    def scan_graph_file(
        cls, file: Path, graphs: Dict[str, QGraphBaseType]
    ) -> None:
        logger.info(f"Scanning graph file {file}")
        try:
            # TODO Think of a safer way to execute the code
            importlib.import_module(file.name)
        except StopInspection:
            graph = cls.last_instantiated_graph
            cls.last_instantiated_graph = None

            if graph is None:
                logger.warning(f"No node instantiated in file {file}")
                return

            graph.filepath = file
            graph.mode.inspection = False
            cls.add_graph(graph, graphs)

    @classmethod
    def add_graph(
        cls,
        graph: "QualibrationGraph",
        graphs: Dict[str, QGraphBaseType],
    ) -> None:
        if graph.name in graphs:
            logger.warning(
                f'Graph "{graph.name}" already exists in library, overwriting'
            )

        graphs[graph.name] = graph

    def _is_execution_finished(self) -> bool:
        return all(
            map(
                lambda state: state == NodeState.successful,
                nx.get_node_attributes(self._graph, "state").values(),
            )
        )

    def run(
        self,
        parameters: Union[GraphParameters, Mapping[str, Any]],
    ) -> None:
        """
        :param parameters: Should be instance of `self.full_parameters` or Mapping
        """
        if self.full_parameters is None:
            raise ValueError("Graph full parameters class have been built")
        if isinstance(parameters, Mapping):
            parameters = self.full_parameters(**parameters)
        nodes_parameters = cast(
            ExecutionParameters, parameters
        ).nodes_parameters
        predecessors = self._graph.pred
        successors = self._graph.succ
        nodes_without_predecessors = filter(
            lambda n: len(predecessors[n]) == 0, predecessors.keys()
        )
        execution_queue: Queue[QualibrationNode] = Queue()
        for node in nodes_without_predecessors:
            execution_queue.put(node)
        while not self._is_execution_finished():
            node_to_run = execution_queue.get()
            if any(
                map(
                    lambda n: self._graph.nodes[n]["state"]
                    != NodeState.successful,
                    predecessors[node_to_run],
                )
            ):
                continue
            node_parameters = node_to_run.parameters_class(
                **getattr(nodes_parameters, node_to_run.name).model_dump()
            )
            # TODO: wrap status of execution
            node_to_run.run(node_parameters)
            new_state = NodeState.successful
            self._graph.nodes[node_to_run]["state"] = new_state
            if new_state == NodeState.successful:
                for successor in successors[node_to_run]:
                    execution_queue.put(successor)
            else:
                execution_queue.put(node_to_run)

    @staticmethod
    def _get_qlibrary_or_error() -> "QualibrationLibrary":
        lib_module = importlib.import_module("qualibrate.qualibration_library")
        qlib_class = lib_module.QualibrationLibrary
        library = qlib_class.active_library
        if library is None:
            raise ValueError("QualibrationLibrary not specified")
        return cast("QualibrationLibrary", library)

    @staticmethod
    def _get_qnode_or_error(
        library: "QualibrationLibrary", node_name: str
    ) -> QualibrationNode:
        node = library.nodes.get(node_name)
        if node is None:
            raise ValueError(f"Unknown node with name {node_name}")
        return node

    def _add_node_by_name(
        self, node_name: str, library: "QualibrationLibrary"
    ) -> QualibrationNode:
        node = self._get_qnode_or_error(library, node_name)
        if node not in self._graph:
            self._graph.add_node(node, **self.__class__._node_init_args)
        return node

    def _build_parameters_class(self) -> None:
        nodes_parameters_class = create_model(
            "GraphNodesParameters",
            __base__=NodesParameters,
            **{  # type: ignore
                node.name: (node.parameters_class, ...)
                for node in self._graph.nodes
            },
        )
        execution_parameters_class = create_model(
            "ExecutionParameters",
            __base__=(self.parameters_class, ExecutionParameters),
            nodes_parameters=(nodes_parameters_class, ...),
        )
        self.full_parameters = execution_parameters_class  # type: ignore

    def serialize(self) -> Mapping[str, Any]:
        if self.full_parameters is None:
            raise ValueError("Graph full parameters class have been built")
        parameters = self.full_parameters.serialize()
        data: Dict[str, Any] = dict(self.export(node_names_only=True))
        data.update(
            {
                "name": self.name,
                "parameters": parameters["parameters"],
            }
        )
        nodes = {}
        connectivity = []
        for node, adjacency in zip(data.pop("nodes"), data.pop("adjacency")):
            node_id = node["id"]
            nodes[node_id] = node
            node.update(
                {
                    # TODO: simplify node name
                    "name": node_id,
                    "parameters": parameters["nodes_parameters"][node["id"]],
                }
            )
            connectivity.extend([(node_id, item["id"]) for item in adjacency])
        data.update({"nodes": nodes, "connectivity": connectivity})
        return data

    def export(self, node_names_only: bool = False) -> Mapping[str, Any]:
        data = dict(nx.readwrite.adjacency_data(self._graph))
        if node_names_only:
            for i, (node, adjacency) in enumerate(
                zip(data["nodes"], data["adjacency"])
            ):
                node["id"] = node["id"].name
                for adj in adjacency:
                    adj["id"] = adj["id"].name
        return data

    def cytoscape_representation(self) -> Sequence[Mapping[str, Any]]:
        serialized = self.serialize()
        nodes = [
            {
                "group": "nodes",
                "data": {"id": node},
                "position": {"x": 100, "y": 100},
            }
            for node in serialized["nodes"]
        ]
        edges = [
            {
                "group": "edges",
                "data": {
                    "id": f"{source}_{dest}",
                    "source": source,
                    "target": dest,
                },
            }
            for source, dest in serialized["connectivity"]
        ]
        return [*nodes, *edges]
