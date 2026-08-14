"""SANI Authority & Policy Engine.

CRITICAL RULE:
1. AuthorityEngine DECIDES; it NEVER EXECUTES commands or tools.
2. AuthorityEngine outputs an AuthorityDecision struct (ALLOW, DENY, POLICY_CONFLICT, REQUIRES_CONFIRMATION).
"""

from typing import Callable
from sani.config import get_config
from sani.models import (
    ActionRiskLevel,
    AuthorityDecision,
    AuthorityDecisionType,
    Role,
    ToolRequest,
    UserIdentity,
)


PolicyRule = Callable[[UserIdentity, ToolRequest, ActionRiskLevel], str | None]


class AuthorityEngine:
    """Pure decision-maker for evaluating user authority, action risk, and policy conflicts."""

    def __init__(self) -> None:
        self._policy_rules: list[PolicyRule] = []

    def register_policy_rule(self, rule: PolicyRule) -> None:
        """Register a custom policy rule function.
        
        Rule functions accept (user, request, risk_level) and return:
        - A string message detailing the conflict if a policy conflict is detected.
        - None if no conflict exists.
        """
        self._policy_rules.append(rule)

    def evaluate(self, request: ToolRequest, risk_level: ActionRiskLevel) -> AuthorityDecision:
        """Evaluate a tool request and produce a deterministic AuthorityDecision.
        
        This method MUST NOT execute any tool or cause system side-effects.
        """
        config = get_config()
        user = request.requested_by

        # 1. User Authorization Check
        if not user.is_authenticated:
            return AuthorityDecision(
                decision=AuthorityDecisionType.DENY,
                reason=f"Unauthenticated session cannot execute '{request.tool_name}'.",
                risk_level=risk_level,
                user_identity=user,
                action_name=request.tool_name,
            )

        # Non-owners attempting DESTRUCTIVE or SYSTEM_CHANGING actions without OWNER role
        if user.role != Role.OWNER and risk_level in (ActionRiskLevel.DESTRUCTIVE, ActionRiskLevel.SYSTEM_CHANGING):
            return AuthorityDecision(
                decision=AuthorityDecisionType.DENY,
                reason=f"User '{user.name}' (Role: {user.role.value}) lacks authority for {risk_level.value} action '{request.tool_name}'. Only OWNER ({config.owner_name}) has this permission.",
                risk_level=risk_level,
                user_identity=user,
                action_name=request.tool_name,
            )

        # 2. Policy Conflict Check
        for policy in self._policy_rules:
            conflict_reason = policy(user, request, risk_level)
            if conflict_reason:
                return AuthorityDecision(
                    decision=AuthorityDecisionType.POLICY_CONFLICT,
                    reason=f"Policy Conflict: {conflict_reason}",
                    risk_level=risk_level,
                    user_identity=user,
                    action_name=request.tool_name,
                )

        # 3. Confirmation Requirement Check
        if risk_level == ActionRiskLevel.DESTRUCTIVE:
            return AuthorityDecision(
                decision=AuthorityDecisionType.REQUIRES_CONFIRMATION,
                reason=f"Action '{request.tool_name}' is DESTRUCTIVE and requires explicit human confirmation.",
                risk_level=risk_level,
                user_identity=user,
                action_name=request.tool_name,
            )

        if risk_level == ActionRiskLevel.SYSTEM_CHANGING and not config.auto_confirm_low_risk:
            return AuthorityDecision(
                decision=AuthorityDecisionType.REQUIRES_CONFIRMATION,
                reason=f"Action '{request.tool_name}' is SYSTEM_CHANGING and requires explicit human confirmation.",
                risk_level=risk_level,
                user_identity=user,
                action_name=request.tool_name,
            )

        # 4. Allowed
        return AuthorityDecision(
            decision=AuthorityDecisionType.ALLOW,
            reason=f"Action '{request.tool_name}' authorized for user '{user.name}'.",
            risk_level=risk_level,
            user_identity=user,
            action_name=request.tool_name,
        )
