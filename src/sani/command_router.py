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
        if not config or not git_tool:
            return CommandOutcome(True, "Push system is not configured.", assessment)

        workspace_root = str(config.workspace_root)

        # Check remote
        remote_url = git_tool.get_remote_url(workspace_root)
        if not remote_url:
            return CommandOutcome(True, "Cannot push to GitHub: No remote repository configured.", assessment)

        # Check for BOTH uncommitted changes AND unpushed commits
        ok, status_out = git_tool._run_git(["status", "--porcelain"], cwd=workspace_root)
        has_uncommitted = bool(ok and status_out and status_out.strip())
        commit_count, unpushed_files = git_tool.list_unpushed_files(workspace_root)
        has_unpushed = commit_count > 0

        if not has_uncommitted and not has_unpushed:
            return CommandOutcome(True, "Everything is already up-to-date with GitHub. Nothing to push.", assessment)

        # Launch the interactive push workflow with GUI
        from sani.tools.push_workflow import PushWorkflowEngine
        workflow = PushWorkflowEngine(git_tool, workspace_root)

        if origin == InputOrigin.VOICE:
            # Announce what was found, then open the GUI
            parts = []
            if has_uncommitted:
                parts.append("uncommitted changes")
            if has_unpushed:
                parts.append(f"{commit_count} unpushed commit(s)")
            summary = " and ".join(parts)
            msg = f"I found {summary}. Opening the push review window now."
            print(f"SANI > {msg}")

        ok, result_msg = workflow.run_interactive()
        return CommandOutcome(True, result_msg, assessment)
