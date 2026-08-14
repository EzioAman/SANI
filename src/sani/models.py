"""SANI Domain Data Models and Schemas."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Role(str, Enum):
    OWNER = "OWNER"  # Primary authority (Aman)
    USER = "USER"    # Standard authenticated user with limited permissions
    GUEST = "GUEST"  # Guest session with minimal permissions


class UserIdentity(BaseModel):
    """Authenticated user identity."""

    user_id: str
    name: str
    role: Role = Role.USER
    is_authenticated: bool = True


class ActionRiskLevel(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"  # Safe read-only state/info queries
    LOW_RISK = "LOW_RISK"            # Safe modifications within sandbox
    SYSTEM_CHANGING = "SYSTEM_CHANGING"  # Modifying code, files, or environment
    DESTRUCTIVE = "DESTRUCTIVE"      # Deleting files, system commands, Git pushes


class AuthorityDecisionType(str, Enum):
    ALLOW = "ALLOW"                      # User authorized & policy permits
    DENY = "DENY"                        # User NOT authorized
    POLICY_CONFLICT = "POLICY_CONFLICT"  # Authorized user, but active policy conflicts
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"  # Permitted, but risk level triggers human confirmation


class AuthorityDecision(BaseModel):
    """Result produced strictly by AuthorityEngine (no side-effects)."""

    decision: AuthorityDecisionType
    reason: str
    risk_level: ActionRiskLevel
    user_identity: UserIdentity
    action_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_executable(self) -> bool:
        """Returns True only if the decision permits immediate execution without further approval."""
        return self.decision == AuthorityDecisionType.ALLOW


class ToolRequest(BaseModel):
    """Tool invocation payload requested by agent reasoning."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    requested_by: UserIdentity
    context: str = ""


class MemoryItem(BaseModel):
    """Persistent memory record with provenance metadata."""

    memory_id: str
    owner_id: str                          # User ID who owns this memory (e.g. Aman)
    memory_type: str                       # INSTRUCTION, PREFERENCE, FACT, INFERENCE
    content: str
    confidence: float = 1.0                # 0.0 to 1.0
    verification_state: str = "UNVERIFIED" # VERIFIED, UNVERIFIED, CONTRADICTED
    superseded_by: str | None = None       # ID of superseding memory if overwritten
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)
