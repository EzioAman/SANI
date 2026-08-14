"""Shared deterministic command routing for typed and voice interfaces."""

from dataclasses import dataclass
from sani.agent import SANIAgent
from sani.models import InputOrigin, UserIdentity
from sani.voice.intent import IntentAssessment, IntentKind, SmartIntentClassifier


@dataclass
class CommandOutcome:
    handled: bool
    message: str = ""
    assessment: IntentAssessment | None = None


@dataclass
class PendingConfirmation:
    action: str
    arguments: dict
    user_id: str
    origin: InputOrigin


class CommandRouter:
    """Proposes commands, binds voice confirmation, and delegates execution to SANIAgent."""

    def __init__(self, agent: SANIAgent, classifier: SmartIntentClassifier | None = None) -> None:
        self.agent = agent
        self.classifier = classifier or SmartIntentClassifier()
        self.pending: PendingConfirmation | None = None

    @staticmethod
    def _clean_text(text: str) -> str:
        import re
        return re.sub(r"[^\w\s]", "", text).strip().lower()

    def _is_confirmation(self, text: str) -> bool:
        cleaned = self._clean_text(text)
        valid_confirmations = {
            "yes",
            "confirm",
            "confirm push",
            "yes push it",
            "yes push",
            "push it now",
            "push it",
            "please push",
            "go ahead",
            "confirm execution",
        }
        return (
            cleaned in valid_confirmations
            or "confirm push" in cleaned
            or "yes push" in cleaned
        )

    def _is_cancellation(self, text: str) -> bool:
        cleaned = self._clean_text(text)
        valid_cancellations = {
            "cancel",
            "never mind",
            "forget it",
            "dont do that",
            "do not do that",
            "abort",
            "stop",
        }
        return (
            cleaned in valid_cancellations
            or cleaned.startswith("cancel")
            or "dont do" in cleaned
        )

    def handle(self, text: str, user: UserIdentity, origin: InputOrigin) -> CommandOutcome:
        if self.pending:
            pending = self.pending
            if pending.user_id != user.user_id:
                return CommandOutcome(True, "That confirmation belongs to a different user.")
            if self._is_cancellation(text):
                self.pending = None
                return CommandOutcome(True, "Cancelled. No action was taken.")
            if self._is_confirmation(text):
                self.pending = None  # Consume before execution: confirmations cannot be replayed.
                decision, result = self.agent.request_tool_execution(
                    pending.action, pending.arguments, user, is_human_confirmed=True, origin=pending.origin
                )
                if result is None:
                    return CommandOutcome(True, f"Action was not executed: {decision.reason}")
                ok, detail = result
                return CommandOutcome(True, "GitHub push completed." if ok else f"GitHub push failed: {detail}")
            self.pending = None
            return CommandOutcome(True, "I did not treat that as confirmation, so the pending action was cancelled.")

        assessment = self.classifier.assess(text)
        if assessment.kind == IntentKind.AMBIGUOUS:
            return CommandOutcome(True, "Do you want me to stop listening or cancel a specific action?", assessment)
        if assessment.action != "git_push":
            return CommandOutcome(False, assessment=assessment)

        config = getattr(self.agent, "config", None)
        git_tool = getattr(self.agent, "git_tool", None)
        if config and git_tool:
            workspace_root = str(config.workspace_root)
            remote_url = git_tool.get_remote_url(workspace_root)
            if not remote_url:
                return CommandOutcome(True, "Cannot push to GitHub: No remote repository configured.", assessment)

            is_safe, safety_msg, sensitive_files = git_tool.inspect_pre_operation_safety(workspace_root)
            if not is_safe:
                return CommandOutcome(True, f"Push blocked for safety: {safety_msg}", assessment)

        pending = PendingConfirmation("git_push", {"remote": "origin", "branch": None}, user.user_id, origin)
        if origin == InputOrigin.VOICE:
            self.pending = pending
            return CommandOutcome(True, "I can push the current branch to GitHub. Say 'confirm push' to continue.", assessment)
        decision, result = self.agent.request_tool_execution("git_push", pending.arguments, user, origin=origin)
        if result is not None:
            ok, detail = result
            return CommandOutcome(True, "GitHub push completed." if ok else f"GitHub push failed: {detail}", assessment)
        if decision.decision.value == "REQUIRES_CONFIRMATION":
            self.pending = pending
            return CommandOutcome(True, "This action requires confirmation. Type 'confirm push' to continue.", assessment)
        return CommandOutcome(True, f"GitHub push was not executed: {decision.reason}", assessment)
