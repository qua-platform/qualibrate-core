import json
from pathlib import Path
from typing import Any

from qualibrate.utils.node.loaders.base_loader import BaseLoader


class JSONLoader(BaseLoader):
    """
    Loader for JSON files.

    Attributes:
        file_extensions: A tuple of supported JSON file extensions
            (e.g., ".json").
    """

    file_extensions = (".json",)

    def load(self, file_path: Path, **kwargs: Any) -> Any:
        """
        Loads a JSON file.

        Args:
            file_path: The path to the JSON file.
            **kwargs: Additional arguments for file loading.

        Returns:
            The parsed JSON content.
        """
        self.__class__.validate_file_exists(file_path)
        with open(file_path) as f:
            return json.load(f)
