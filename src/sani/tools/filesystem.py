"""SANI Filesystem Tools with Independent Parameter Validation."""

import difflib
from pathlib import Path
from sani.config import get_config


def _validate_path_in_workspace(path_str: str) -> Path:
    """Independent parameter validation: Ensure target path resides within workspace root."""
    config = get_config()
    target_path = Path(path_str).resolve()
    workspace_root = config.workspace_root.resolve()

    try:
        target_path.relative_to(workspace_root)
    except ValueError:
        raise ValueError(
            f"Path Security Violation: Path '{path_str}' is outside allowed workspace root '{workspace_root}'."
        )

    return target_path


def read_file(path: str) -> str:
    """Read contents of a text file within workspace."""
    target_path = _validate_path_in_workspace(path)
    if not target_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not target_path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    return target_path.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    """Write content to a text file within workspace."""
    target_path = _validate_path_in_workspace(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    return f"Successfully wrote {len(content)} characters to {target_path.name}"


def generate_diff(path: str, new_content: str) -> str:
    """Generate unified diff preview before updating a file."""
    target_path = _validate_path_in_workspace(path)
    old_content = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

    diff_lines = list(
        difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{target_path.name}",
            tofile=f"b/{target_path.name}",
        )
    )
    return "".join(diff_lines) if diff_lines else "No changes."


def list_directory(path: str = ".") -> list[str]:
    """List directory contents within workspace."""
    target_path = _validate_path_in_workspace(path)
    if not target_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not target_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    return [p.name for p in target_path.iterdir()]
