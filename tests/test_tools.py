"""Unit tests for independent tool parameter validation."""

import pytest
from sani.tools.filesystem import read_file, write_file


def test_filesystem_tool_rejects_out_of_bounds_path(tmp_path) -> None:
    # Attempt to write outside workspace
    outside_file = str(tmp_path / "outside.txt")
    
    with pytest.raises(ValueError, match="Path Security Violation"):
        write_file(outside_file, "malicious content")

    with pytest.raises(ValueError, match="Path Security Violation"):
        read_file(outside_file)
