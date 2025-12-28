from __future__ import annotations

import inspect
import sys
from functools import lru_cache
from typing import Any

__all__ = [
    "enable_inspect_cache",
    "disable_inspect_cache",
    "clear_inspect_cache",
    "get_cache_stats",
]


def enable_inspect_cache() -> None:
    """
    Enable caching for inspect module functions.

    This should be called before library scanning to improve performance.
    Call `disable_inspect_cache()` after scanning is complete.
    """
    global _cache_enabled
    if _cache_enabled:
        return

    inspect.getmodule = _cached_getmodule  # type: ignore[assignment]
    inspect.getsourcefile = _cached_getsourcefile  # type: ignore[assignment]
    inspect.getsourcelines = _cached_getsourcelines  # type: ignore[assignment]
    inspect.getfile = _cached_getfile_wrapper  # type: ignore[assignment]
    _cache_enabled = True


def disable_inspect_cache() -> None:
    """
    Disable caching and restore original inspect functions.

    This should be called after library scanning is complete.
    """
    global _cache_enabled
    if not _cache_enabled:
        return

    inspect.getmodule = _original_getmodule
    inspect.getsourcefile = _original_getsourcefile
    inspect.getsourcelines = _original_getsourcelines
    inspect.getfile = _original_getfile
    _cache_enabled = False


def clear_inspect_cache() -> None:
    """Clear all inspection caches."""
    _cached_getmodule_by_file.cache_clear()
    _cached_getsourcefile_by_module.cache_clear()
    _cached_getfile.cache_clear()
    _sourcelines_cache.clear()


def get_cache_stats() -> dict[str, Any]:
    """Get statistics about cache usage."""
    return {
        "enabled": _cache_enabled,
        "getmodule_cache": _cached_getmodule_by_file.cache_info(),
        "getsourcefile_cache": _cached_getsourcefile_by_module.cache_info(),
        "getfile_cache": _cached_getfile.cache_info(),
        "sourcelines_cache_size": len(_sourcelines_cache),
    }


# Store original functions
_original_getmodule = inspect.getmodule
_original_getsourcefile = inspect.getsourcefile
_original_getsourcelines = inspect.getsourcelines
_original_getfile = inspect.getfile

# Track if caching is enabled
_cache_enabled = False


@lru_cache(maxsize=1024)
def _cached_getmodule_by_file(filename: str) -> Any:
    """Cache getmodule results by filename."""
    # Find module by checking sys.modules
    for _name, module in list(sys.modules.items()):
        try:
            module_file = getattr(module, "__file__", None)
            if module_file and module_file == filename:
                return module
        except Exception:
            continue
    return None


def _cached_getmodule(obj: Any, _filename: str | None = None) -> Any:
    """Cached version of inspect.getmodule."""
    # Try to get filename for caching
    try:
        if _filename is None:
            _filename = _original_getsourcefile(obj)
        if _filename:
            cached = _cached_getmodule_by_file(_filename)
            if cached is not None:
                return cached
    except Exception:
        pass
    # Fall back to original
    return _original_getmodule(obj, _filename)


@lru_cache(maxsize=512)
def _cached_getsourcefile_by_module(module_name: str) -> str | None:
    """Cache getsourcefile by module name."""
    if module_name in sys.modules:
        module = sys.modules[module_name]
        return _original_getsourcefile(module)
    return None


def _cached_getsourcefile(obj: Any) -> str | None:
    """Cached version of inspect.getsourcefile."""
    # Try to use module-based cache for classes
    if isinstance(obj, type):
        module_name = getattr(obj, "__module__", None)
        if module_name:
            cached = _cached_getsourcefile_by_module(module_name)
            if cached is not None:
                return cached
    # Fall back to original
    return _original_getsourcefile(obj)


# Cache for source lines - key is (filename, class_qualname)
_sourcelines_cache: dict[tuple[str, str], tuple[list[str], int]] = {}


def _cached_getsourcelines(obj: Any) -> tuple[list[str], int]:
    """Cached version of inspect.getsourcelines."""
    try:
        # Get source file
        filename = _cached_getsourcefile(obj)
        if filename:
            # Create cache key
            qualname = getattr(obj, "__qualname__", str(obj))
            cache_key = (filename, qualname)

            if cache_key in _sourcelines_cache:
                return _sourcelines_cache[cache_key]

            # Get and cache
            result = _original_getsourcelines(obj)
            _sourcelines_cache[cache_key] = result
            return result
    except Exception:
        pass
    # Fall back to original
    return _original_getsourcelines(obj)


@lru_cache(maxsize=512)
def _cached_getfile(obj: Any) -> str:
    """Cached version of inspect.getfile for hashable objects."""
    return _original_getfile(obj)


def _cached_getfile_wrapper(obj: Any) -> str:
    """Wrapper that handles non-hashable objects."""
    try:
        # For types and modules, use cached version
        if isinstance(obj, type | type(sys)):
            return _cached_getfile(obj)
    except TypeError:
        pass
    return _original_getfile(obj)
