"""SANI Controlled Terminal Execution Tool."""

import subprocess
from sani.config import get_config


def execute_terminal_command(command: str) -> str:
    """Execute shell command within workspace directory.
    
    Independently validates command parameters before invocation.
    """
    if not command or not command.strip():
        raise ValueError("Command cannot be empty.")

    config = get_config()
    cwd = str(config.workspace_root)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Terminal command timed out after 60s: '{command}'")
