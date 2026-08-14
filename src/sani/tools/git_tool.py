"""Git Operations Tool with Automatic Executable Resolution & SANI Authority Guardrails."""

import os
import shutil
import subprocess
from sani.models import ActionRiskLevel
from sani.tools.registry import ToolDefinition


class GitTool:
    """Tool wrapper for git status, diff, commit, audit, and remote push."""

    def __init__(self, git_path: str | None = None) -> None:
        self.git_path = git_path or self._find_git_executable()

    @staticmethod
    def _find_git_executable() -> str:
        """Locate git.exe on Windows or system PATH."""
        # 1. Check system PATH
        path_git = shutil.which("git")
        if path_git:
            return path_git

        # 2. Check standard Windows Git install locations
        common_paths = [
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Git\cmd\git.exe"),
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p

        return "git"

    def _run_git(self, args: list[str], cwd: str) -> tuple[bool, str]:
        try:
            res = subprocess.run(
                [self.git_path] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True, res.stdout.strip()
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() or e.stdout.strip()
            return False, f"Git error: {err}"
        except Exception as ex:
            return False, f"Git execution failed: {ex}"

    def status(self, workspace_root: str) -> str:
        """Return git repository status."""
        ok, out = self._run_git(["status"], cwd=workspace_root)
        return out

    def get_commit_log(self, workspace_root: str, count: int = 1) -> str:
        """Return recent commit log."""
        ok, out = self._run_git(["log", f"-n{count}", "--oneline"], cwd=workspace_root)
        return out

    def get_remote_url(self, workspace_root: str, remote: str = "origin") -> str:
        """Return remote repository URL."""
        ok, out = self._run_git(["remote", "get-url", remote], cwd=workspace_root)
        return out if ok else ""

    def push(self, workspace_root: str, remote: str = "origin", branch: str = "main") -> tuple[bool, str]:
        """Push commits to remote repository (Requires Aman Confirmation)."""
        ok, out = self._run_git(["push", "-u", remote, branch], cwd=workspace_root)
        return ok, out

    def push_with_credentials(
        self, workspace_root: str, remote_url: str, username: str, token_or_pass: str, branch: str = "main"
    ) -> tuple[bool, str]:
        """Push to remote URL with embedded PAT token or password credentials."""
        # Replace https:// with https://username:token@ in remote URL
        clean_url = remote_url.replace("https://", "").replace("http://", "")
        auth_url = f"https://{username}:{token_or_pass}@{clean_url}"
        
        ok, out = self._run_git(["push", "--set-upstream", auth_url, branch], cwd=workspace_root)
        return ok, out


def get_git_tool_definitions() -> list[ToolDefinition]:
    """Return tool definitions for Git operations."""
    return [
        ToolDefinition(
            name="git_status",
            description="Inspect git workspace status and untracked changes.",
            risk_level=ActionRiskLevel.INFORMATIONAL,
            parameters_schema={"type": "object", "properties": {}},
        ),
        ToolDefinition(
            name="git_push",
            description="Push local git commits to remote GitHub repository.",
            risk_level=ActionRiskLevel.SYSTEM_CHANGING,
            parameters_schema={
                "type": "object",
                "properties": {
                    "remote": {"type": "string", "default": "origin"},
                    "branch": {"type": "string", "default": "main"},
                },
            },
        ),
    ]
