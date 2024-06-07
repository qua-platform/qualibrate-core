from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LibraryScanException(RuntimeError):
    pass


def file_is_calibration_node(file: Path):
    if not file.is_file():
        return False
    if file.suffix != ".py":
        return False

    contents = file.read_text()
    if "QualibrationNode(" not in contents:
        return False
    return True


class QualibrationLibrary:
    active_library: "QualibrationLibrary" = None

    def __init__(self, library_folder: Optional[Path] = None, set_active=True):
        self.nodes = {}

        if set_active:
            QualibrationLibrary.active_library = self

        if library_folder:
            self.scan_folder_for_nodes(library_folder)

    def scan_folder_for_nodes(self, path: Path, append=False):
        if isinstance(path, str):
            path = Path(path)

        if not append:
            self.nodes = {}

        try:
            from qualibrate import QualibrationNode

            original_mode = QualibrationNode.mode
            QualibrationNode.mode = "library_scan"

            for file in sorted(path.iterdir()):
                if not file_is_calibration_node(file):
                    continue
                self.scan_node_file(file)
        finally:
            QualibrationNode.mode = original_mode

    def scan_node_file(self, file: Path):
        logging.info(f"Scanning node file {file}")
        with file.open() as f:
            code = f.read()

        try:
            # TODO Think of a safer way to execute the code
            exec(code)
        except LibraryScanException:
            pass

    def add_node(self, node):
        if node.name in self.nodes:
            logger.warning(f'Node "{node.name}" already exists in library, overwriting')

        self.nodes[node.name] = node