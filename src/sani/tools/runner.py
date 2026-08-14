"""SANI Tool Execution Runtime.

CRITICAL RULES:
1. ToolRunner EXECUTES tools; it NEVER decides authority.
2. ToolRunner requires an explicit AuthorityDecision before attempting execution.
3. Execution proceeds ONLY if decision is ALLOW (or explicit out-of-band confirmation is provided).
"""

from typing import Any
from sani.models import AuthorityDecision, AuthorityDecisionType, ToolRequest
from sani.tools.registry import ToolRegistry


class ExecutionDeniedError(PermissionError):
    """Raised when execution is attempted on a DENIED or POLICY_CONFLICT decision."""
    pass


class ConfirmationRequiredException(Exception):
    """Raised when execution is attempted on a decision requiring human confirmation."""

    def __init__(self, decision: AuthorityDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class ToolRunner:
    """Execution engine responsible for invoking tools once authorized by AuthorityEngine."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(
        self,
        request: ToolRequest,
        decision: AuthorityDecision,
        is_human_confirmed: bool = False,
    ) -> Any:
        """Execute the tool request if permitted by the decision.
        
        This method DOES NOT evaluate authority; it enforces the decision made by AuthorityEngine.
        """
        # Enforce Authority Decision
        if decision.decision == AuthorityDecisionType.DENY:
            raise ExecutionDeniedError(f"Execution DENIED: {decision.reason}")

        if decision.decision == AuthorityDecisionType.POLICY_CONFLICT:
            raise ExecutionDeniedError(f"Execution blocked due to POLICY CONFLICT: {decision.reason}")

        if decision.decision == AuthorityDecisionType.REQUIRES_CONFIRMATION and not is_human_confirmed:
            raise ConfirmationRequiredException(decision)

        tool_def = self.registry.get_tool(request.tool_name)
        if not tool_def:
            raise ValueError(f"Tool '{request.tool_name}' is not registered in ToolRegistry.")

        # Execute Tool (Parameter validation happens independently within the tool function)
        return tool_def.func(**request.arguments)
