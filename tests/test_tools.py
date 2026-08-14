"""Unit tests for independent tool parameter validation."""

import pytest
from sani.config import get_config
from sani.tools.filesystem import read_file, write_file


def test_filesystem_tool_rejects_out_of_bounds_path() -> None:
    # Attempt to write outside workspace
    outside_file = str(get_config().workspace_root.parent / "outside_sani_workspace.txt")
    
    with pytest.raises(ValueError, match="Path Security Violation"):
        write_file(outside_file, "malicious content")

    with pytest.raises(ValueError, match="Path Security Violation"):
        read_file(outside_file)
