"""Unit tests for SANI system inspection and publishing tools."""

import pytest
from sani.agent import SANIAgent
from sani.models import Role, UserIdentity
from sani.tools.system_tools import (
    git_publish,
    git_set_remote,
    inspect_system_status,
    inspect_system_tools,
)


@pytest.fixture
def owner_user() -> UserIdentity:
    return UserIdentity(user_id="aman_01", name="Aman", role=Role.OWNER)


def test_inspect_system_tools(owner_user: UserIdentity) -> None:
    agent = SANIAgent()
    output = inspect_system_tools(agent)

    assert "Registered SANI Tools:" in output
    assert "git_push" in output
    assert "git_publish" in output
    assert "git_set_remote" in output
    assert "inspect_system_tools" in output
    assert "inspect_system_status" in output
    assert "read_file" in output
    assert "write_file" in output


def test_inspect_system_status(owner_user: UserIdentity) -> None:
    agent = SANIAgent()
    status_str = inspect_system_status(agent)

    assert "SANI System Status:" in status_str
    assert "Primary Owner:" in status_str
    assert "LLM Provider:" in status_str
    assert "Registered Tools:" in status_str


def test_git_set_remote(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    monkeypatch.setattr(agent.git_tool, "set_remote_url", lambda root, remote_url, remote_name="origin": (True, f"Added remote '{remote_name}' with {remote_url}"))

    result = git_set_remote(agent, "https://github.com/EzioAman/SANI.git")
    assert "Added remote 'origin' with https://github.com/EzioAman/SANI.git" in result


def test_git_publish_no_remote_returns_error(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    monkeypatch.setattr(agent.git_tool, "get_remote_url", lambda root, remote="origin": "")

    result = git_publish(agent)
    assert "No Git remote configured" in result


def test_command_router_detects_github_url(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    from sani.command_router import CommandRouter, InputOrigin
    agent = SANIAgent()
    router = CommandRouter(agent)

    monkeypatch.setattr(agent.git_tool, "set_remote_url", lambda root, remote_url, remote_name="origin": (True, f"Set {remote_url}"))

    outcome = router.handle("set remote to https://github.com/EzioAman/SANI.git", owner_user, InputOrigin.TYPED)
    assert outcome.handled
    assert "Successfully configured Git remote URL to https://github.com/EzioAman/SANI.git" in outcome.message
