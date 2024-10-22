import logging
from pathlib import Path

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    from qualibrate import NodeParameters, QualibrationLibrary, QualibrationNode

    library_folder = Path(__file__).parent.parent / "calibrations"
    library = QualibrationLibrary[QualibrationNode[NodeParameters]](
        library_folder=library_folder
    )

    print(library.nodes)
