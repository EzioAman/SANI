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

    def get_current_branch(self, workspace_root: str) -> str:
        """Return the currently checked-out branch, or an empty string when detached."""
        ok, out = self._run_git(["branch", "--show-current"], cwd=workspace_root)
        return out if ok else ""

    def inspect_pre_operation_safety(self, workspace_root: str) -> tuple[bool, str, list[str]]:
        """Inspect workspace for secrets and sensitive files before any commit or push operation."""
        sensitive_patterns = [
            r"\.env$",
            r"\.env\.",
            r"\.db$",
            r"\.sqlite",
            r"\.pem$",
            r"\.key$",
            r"\.pfx$",
            r"\.p12$",
            r"id_rsa",
            r"id_ed25519",
            r"sani_memory\.db",
            r"secret",
            r"credential",
            r"token",
        ]
        import re

        sensitive_files: set[str] = set()

        # 1. Inspect untracked, modified, and staged files via git status --porcelain
        ok, status_out = self._run_git(["status", "--porcelain"], cwd=workspace_root)
        if ok and status_out:
            for line in status_out.splitlines():
                if len(line) >= 3:
                    file_path = line[3:].strip()
                    base_name = os.path.basename(file_path).lower()
                    for pattern in sensitive_patterns:
                        if re.search(pattern, base_name, re.IGNORECASE) or re.search(pattern, file_path.lower(), re.IGNORECASE):
                            sensitive_files.add(file_path)

        # 2. Inspect files in HEAD commit
        ok_log, log_out = self._run_git(["log", "-n", "1", "--name-only", "--pretty=format:"], cwd=workspace_root)
        if ok_log and log_out:
            for line in log_out.splitlines():
                line = line.strip()
                if line:
                    base_name = os.path.basename(line).lower()
                    for pattern in sensitive_patterns:
                        if re.search(pattern, base_name, re.IGNORECASE) or re.search(pattern, line.lower(), re.IGNORECASE):
                            sensitive_files.add(line)

        if sensitive_files:
            file_list = sorted(list(sensitive_files))
            return False, f"Sensitive file(s) detected: {', '.join(file_list)}. Operation blocked for security.", file_list

        return True, "Pre-operation secret scan passed cleanly.", []

    def push(self, workspace_root: str, remote: str = "origin", branch: str | None = None) -> tuple[bool, str]:
        """Push commits to remote repository with pre-push safety and secret checks."""
        # 1. Pre-push secret check
        is_safe, safety_msg, sensitive_files = self.inspect_pre_operation_safety(workspace_root)
        if not is_safe:
            return False, safety_msg

        # 2. Verify remote exists
        remote_url = self.get_remote_url(workspace_root, remote=remote)
        if not remote_url:
            return False, f"No Git remote repository configured for '{remote}'."

        # 3. Verify current branch
        branch = branch or self.get_current_branch(workspace_root)
        if not branch:
            return False, "Cannot push while HEAD is detached; check out a branch first."

        ok, out = self._run_git(["push", "-u", remote, branch], cwd=workspace_root)
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
