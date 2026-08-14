"""Regression tests for safe Git command selection."""

from sani.tools.git_tool import GitTool


def test_push_uses_current_branch_when_not_supplied(monkeypatch) -> None:
    tool = GitTool(git_path="git")
    calls: list[list[str]] = []

    def fake_run(args: list[str], cwd: str) -> tuple[bool, str]:
        calls.append(args)
        if args == ["branch", "--show-current"]:
            return True, "feature/voice"
        return True, "pushed"

    monkeypatch.setattr(tool, "_run_git", fake_run)
    monkeypatch.setattr(tool, "inspect_pre_operation_safety", lambda cwd: (True, "OK", []))
    monkeypatch.setattr(tool, "get_remote_url", lambda cwd, remote="origin": "https://github.com/EzioAman/SANI.git")

    assert tool.push("workspace") == (True, "pushed")
    assert ["push", "-u", "origin", "feature/voice"] in calls


def test_push_refuses_detached_head(monkeypatch) -> None:
    tool = GitTool(git_path="git")
    monkeypatch.setattr(tool, "inspect_pre_operation_safety", lambda cwd: (True, "OK", []))
    monkeypatch.setattr(tool, "get_remote_url", lambda cwd, remote="origin": "https://github.com/EzioAman/SANI.git")
    monkeypatch.setattr(tool, "get_current_branch", lambda _: "")

    ok, message = tool.push("workspace")

    assert not ok
    assert "detached" in message
