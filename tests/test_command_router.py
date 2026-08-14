"""Safety regressions for shared typed/voice command handling."""

from sani.command_router import CommandRouter
from sani.models import ActionRiskLevel, AuthorityDecision, AuthorityDecisionType, InputOrigin, Role, UserIdentity
from sani.voice.intent import IntentKind, SmartIntentClassifier


def owner() -> UserIdentity:
    return UserIdentity(user_id="aman", name="Aman", role=Role.OWNER)


class FakeAgent:
    def __init__(self) -> None:
        self.calls = []

    def request_tool_execution(self, tool_name, arguments, user, is_human_confirmed=False, origin=InputOrigin.TYPED):
        self.calls.append((tool_name, arguments, is_human_confirmed, origin))
        decision = AuthorityDecision(
            decision=AuthorityDecisionType.ALLOW,
            reason="allowed",
            risk_level=ActionRiskLevel.SYSTEM_CHANGING,
            user_identity=user,
            action_name=tool_name,
        )
        return decision, (True, "ok")


def test_ambiguous_and_discussion_phrases_never_propose_execution() -> None:
    classifier = SmartIntentClassifier()
    for phrase in (
        "oh please stop", "stop being annoying", "you can stop now", "I was joking",
        "don't do that", "that's enough", "leave it", "forget it", "never mind", "cancel",
        "abort", "kill it", "shutdown", "go ahead", "do it", "yeah do that", "push that",
        "I joked that you should push the update to GitHub", "Should I push the project to GitHub?",
    ):
        assert classifier.assess(phrase).action != "git_push"


def test_voice_push_requires_pending_explicit_confirmation() -> None:
    agent = FakeAgent()
    router = CommandRouter(agent)
    first = router.handle("Push the latest update to GitHub.", owner(), InputOrigin.VOICE)
    assert first.handled and agent.calls == []
    assert router.handle("go ahead", owner(), InputOrigin.VOICE).handled
    assert agent.calls == []

    router.handle("Push the latest update to GitHub.", owner(), InputOrigin.VOICE)
    result = router.handle("confirm push", owner(), InputOrigin.VOICE)
    assert result.message == "GitHub push completed."
    assert agent.calls == [("git_push", {"remote": "origin", "branch": None}, True, InputOrigin.VOICE)]


def test_typed_and_voice_use_the_same_normalized_git_action() -> None:
    agent = FakeAgent()
    router = CommandRouter(agent)
    router.handle("Push the latest update to GitHub.", owner(), InputOrigin.TYPED)
    router.handle("Push the latest update to GitHub.", owner(), InputOrigin.VOICE)
    router.handle("yes", owner(), InputOrigin.VOICE)
    assert [call[0] for call in agent.calls] == ["git_push", "git_push"]
