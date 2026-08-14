"""Unit tests for AuthorityEngine (Decision-only engine)."""

import pytest
from sani.authority import AuthorityEngine
from sani.models import (
    ActionRiskLevel,
    AuthorityDecisionType,
    Role,
    ToolRequest,
    UserIdentity,
)


@pytest.fixture
def authority_engine() -> AuthorityEngine:
    return AuthorityEngine()


@pytest.fixture
def owner_user() -> UserIdentity:
    return UserIdentity(user_id="u1", name="Aman", role=Role.OWNER)


@pytest.fixture
def standard_user() -> UserIdentity:
    return UserIdentity(user_id="u2", name="GuestUser", role=Role.USER)


def test_unauthenticated_user_denied(authority_engine: AuthorityEngine) -> None:
    unauth_user = UserIdentity(user_id="u0", name="Anon", role=Role.GUEST, is_authenticated=False)
    request = ToolRequest(tool_name="read_file", requested_by=unauth_user)
    
    decision = authority_engine.evaluate(request, ActionRiskLevel.INFORMATIONAL)
    assert decision.decision == AuthorityDecisionType.DENY
    assert "Unauthenticated" in decision.reason


def test_informational_action_allowed_for_owner(authority_engine: AuthorityEngine, owner_user: UserIdentity) -> None:
    request = ToolRequest(tool_name="read_file", requested_by=owner_user)
    
    decision = authority_engine.evaluate(request, ActionRiskLevel.INFORMATIONAL)
    assert decision.decision == AuthorityDecisionType.ALLOW


def test_non_owner_denied_destructive_action(authority_engine: AuthorityEngine, standard_user: UserIdentity) -> None:
    request = ToolRequest(tool_name="execute_terminal_command", requested_by=standard_user)
    
    decision = authority_engine.evaluate(request, ActionRiskLevel.DESTRUCTIVE)
    assert decision.decision == AuthorityDecisionType.DENY
    assert "lacks authority" in decision.reason


def test_destructive_action_requires_confirmation_for_owner(
    authority_engine: AuthorityEngine, owner_user: UserIdentity
) -> None:
    request = ToolRequest(tool_name="execute_terminal_command", requested_by=owner_user)
    
    decision = authority_engine.evaluate(request, ActionRiskLevel.DESTRUCTIVE)
    assert decision.decision == AuthorityDecisionType.REQUIRES_CONFIRMATION


def test_policy_conflict_takes_precedence(authority_engine: AuthorityEngine, owner_user: UserIdentity) -> None:
    # Register a moral / safety policy rule
    def block_production_db_delete(user: UserIdentity, request: ToolRequest, risk: ActionRiskLevel) -> str | None:
        if "delete_prod" in request.arguments.get("cmd", ""):
            return "Production database deletion is forbidden by Policy Rule #104."
        return None

    authority_engine.register_policy_rule(block_production_db_delete)

    request = ToolRequest(
        tool_name="execute_terminal_command",
        arguments={"cmd": "delete_prod"},
        requested_by=owner_user,
    )
    
    decision = authority_engine.evaluate(request, ActionRiskLevel.DESTRUCTIVE)
    assert decision.decision == AuthorityDecisionType.POLICY_CONFLICT
    assert "Policy Rule #104" in decision.reason
