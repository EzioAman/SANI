"""Unit tests for ToolRunner and ToolRegistry."""

import pytest
from sani.models import (
    ActionRiskLevel,
    AuthorityDecision,
    AuthorityDecisionType,
    Role,
    ToolRequest,
    UserIdentity,
)
from sani.tools.registry import ToolRegistry
from sani.tools.runner import ConfirmationRequiredException, ExecutionDeniedError, ToolRunner


@pytest.fixture
def owner_user() -> UserIdentity:
    return UserIdentity(user_id="u1", name="Aman", role=Role.OWNER)


@pytest.fixture
def tool_runner() -> ToolRunner:
    registry = ToolRegistry()
    registry.register(
        name="echo_tool",
        description="Simple echo tool",
        risk_level=ActionRiskLevel.INFORMATIONAL,
        func=lambda msg: f"Echo: {msg}",
    )
    return ToolRunner(registry)


def test_runner_executes_allowed_decision(tool_runner: ToolRunner, owner_user: UserIdentity) -> None:
    request = ToolRequest(tool_name="echo_tool", arguments={"msg": "hello"}, requested_by=owner_user)
    decision = AuthorityDecision(
        decision=AuthorityDecisionType.ALLOW,
        reason="Permitted",
        risk_level=ActionRiskLevel.INFORMATIONAL,
        user_identity=owner_user,
        action_name="echo_tool",
    )

    result = tool_runner.execute(request, decision)
    assert result == "Echo: hello"


def test_runner_blocks_denied_decision(tool_runner: ToolRunner, owner_user: UserIdentity) -> None:
    request = ToolRequest(tool_name="echo_tool", arguments={"msg": "hello"}, requested_by=owner_user)
    decision = AuthorityDecision(
        decision=AuthorityDecisionType.DENY,
        reason="Access denied",
        risk_level=ActionRiskLevel.DESTRUCTIVE,
        user_identity=owner_user,
        action_name="echo_tool",
    )

    with pytest.raises(ExecutionDeniedError, match="Execution DENIED"):
        tool_runner.execute(request, decision)


def test_runner_requires_confirmation(tool_runner: ToolRunner, owner_user: UserIdentity) -> None:
    request = ToolRequest(tool_name="echo_tool", arguments={"msg": "hello"}, requested_by=owner_user)
    decision = AuthorityDecision(
        decision=AuthorityDecisionType.REQUIRES_CONFIRMATION,
        reason="High risk action",
        risk_level=ActionRiskLevel.DESTRUCTIVE,
        user_identity=owner_user,
        action_name="echo_tool",
    )

    # Fails when unconfirmed
    with pytest.raises(ConfirmationRequiredException):
        tool_runner.execute(request, decision, is_human_confirmed=False)

    # Succeeds when confirmed out-of-band
    result = tool_runner.execute(request, decision, is_human_confirmed=True)
    assert result == "Echo: hello"
