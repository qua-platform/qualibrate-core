from collections.abc import Mapping
from os import PathLike
from pathlib import Path
from typing import Any, Optional


def get_node_dir_path(id: int, base_path: Path) -> Optional[Path]:
    """
    Retrieves the directory path for a specific node ID.

    Args:
        id: The node's identifier.
        base_path: The base directory to search for the node.

    Returns:
        The path to the node's directory if found, or None if no match exists.
    """
    node_path = next(base_path.glob(f"*/#{id}_*"), None)
    return Path(node_path) if node_path is not None else None


def get_node_filepath(node_path: Path) -> Path:
    """
    Constructs the file path to the node's JSON file.

    Args:
        node_path: The directory containing the node.

    Returns:
        The path to the "node.json" file within the specified directory.
    """
    return node_path / "node.json"


def get_data_filepath(node_path: Path) -> Path:
    """
    Constructs the file path to the data JSON file of the node.

    Args:
        node_path: The directory containing the node.

    Returns:
        The path to the "data.json" file within the specified directory.
    """
    return node_path / "data.json"


def get_node_quam_filepath(
    node_data: Mapping[str, Any], node_dir: Path
) -> Optional[Path]:
    """
    Resolves the file path to the QUAM state file for a node.

    Args:
        node_data: A mapping containing node info, including the "quam" path.
        node_dir: The directory containing the node.

    Returns:
        The resolved file path to the QUAM state file if it exists and is a
        file, or None if the file is not found.
    """
    quam_relative_path = node_data.get("quam", "./state.json")
    quam_file_path = resolve_and_check_relative(
        node_dir, Path(quam_relative_path)
    )
    if quam_file_path.is_file():
        return quam_file_path
    return None


def resolve_and_check_relative(base_path: Path, subpath: PathLike[str]) -> Path:
    """
    Build full path from base path and subpath. Raise error if build path isn't
    subpath of base path.

    Raises:
        ValueError: Built path isn't subpath of base path.
    """
    full = (base_path / Path(subpath)).resolve()
    if not full.is_relative_to(base_path):
        raise FileNotFoundError(f"Subpath {subpath} isn't relative to base.")
    return full
