from pathlib import Path
import logging
import qm
from qualibrate import QualibrationLibrary

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    library = QualibrationLibrary()

    assert QualibrationLibrary.active_library == library

    calibrations_folder = Path(__file__).parent / "calibrations"

    library.scan_folder_for_nodes(calibrations_folder)

    print("\nCalibrations:")
    for key, val in library.nodes.items():
        print(f"- {key}: {val}")
