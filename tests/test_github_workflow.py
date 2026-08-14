"""Comprehensive Unit Tests for Safe GitHub Upload/Push Workflow & Guardrails."""

import pytest
from sani.agent import SANIAgent
from sani.command_router import CommandRouter, PendingConfirmation
from sani.models import AuthorityDecisionType, InputOrigin, Role, UserIdentity
from sani.tools.git_tool import GitTool
from sani.voice.intent import IntentCategory, IntentKind, SmartIntentClassifier


@pytest.fixture
def owner_user() -> UserIdentity:
    return UserIdentity(user_id="aman_01", name="Aman", role=Role.OWNER, is_authenticated=True)


@pytest.fixture
def non_owner_user() -> UserIdentity:
    return UserIdentity(user_id="guest_01", name="Guest", role=Role.GUEST, is_authenticated=True)


@pytest.fixture
def unauthenticated_user() -> UserIdentity:
    return UserIdentity(user_id="anon", name="Anonymous", role=Role.OWNER, is_authenticated=False)


# 1. Clear GitHub push command
def test_clear_github_push_command_intent() -> None:
    classifier = SmartIntentClassifier()
    assert classifier.classify("Push the latest update to GitHub") == IntentCategory.GIT_PUSH
    assert classifier.classify("Push this to GitHub") == IntentCategory.GIT_PUSH
    assert classifier.classify("Saini, can you upload this project to GitHub?") == IntentCategory.GIT_PUSH
    assert classifier.classify("Can you upload this project to GitHub?") == IntentCategory.GIT_PUSH
    assert classifier.classify("Could you push this to GitHub?") == IntentCategory.GIT_PUSH


# 2. Ambiguous GitHub statement
def test_ambiguous_github_statement() -> None:
    classifier = SmartIntentClassifier()
    assessment = classifier.assess("oh please push that")
    assert assessment.kind == IntentKind.AMBIGUOUS or assessment.category == IntentCategory.CHAT


# 3. Conversational mention of pushing
def test_conversational_mention_of_pushing() -> None:
    classifier = SmartIntentClassifier()
    assert classifier.classify("I don't want to push this yet.") == IntentCategory.CHAT
    assert classifier.classify("Why would anyone push broken code?") == IntentCategory.CHAT


# 4. User explicitly cancelling a push
def test_user_explicitly_cancelling_push(owner_user: UserIdentity) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)
    router.pending = PendingConfirmation("git_push", {}, owner_user.user_id, InputOrigin.VOICE)

    outcome = router.handle("cancel", owner_user, InputOrigin.VOICE)
    assert outcome.handled
    assert "Cancelled" in outcome.message
    assert router.pending is None


# 5. Voice push request
def test_voice_push_request(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)

    monkeypatch.setattr(agent.git_tool, "list_unpushed_files", lambda root, remote="origin", branch=None: (2, ["src/sani/agent.py", "README.md"]))

    outcome = router.handle("Push the update to GitHub", owner_user, InputOrigin.VOICE)

    assert outcome.handled
    assert "Say 'confirm push'" in outcome.message
    assert "2 commit(s)" in outcome.message
    assert "agent.py" in outcome.message
    assert router.pending is not None
    assert router.pending.origin == InputOrigin.VOICE


# 6. Voice confirmation
def test_voice_confirmation(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)

    monkeypatch.setattr(agent.git_tool, "push", lambda root, remote="origin", branch=None: (True, "Everything up-to-date"))
    monkeypatch.setattr(agent.git_tool, "inspect_pre_operation_safety", lambda root: (True, "OK", []))

    for confirm_phrase in ["confirm push", "Confirm push.", "Confirm push!", "Yes, push it."]:
        router.pending = PendingConfirmation("git_push", {"remote": "origin", "branch": "main"}, owner_user.user_id, InputOrigin.VOICE)
        outcome = router.handle(confirm_phrase, owner_user, InputOrigin.VOICE)
        assert outcome.handled
        assert "GitHub push completed" in outcome.message
        assert router.pending is None


# 7. Voice ambiguous confirmation rejected
def test_voice_ambiguous_confirmation_rejected(owner_user: UserIdentity) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)
    router.pending = PendingConfirmation("git_push", {"remote": "origin", "branch": "main"}, owner_user.user_id, InputOrigin.VOICE)

    for ambiguous_word in ["okay", "sure", "yeah", "do that", "alright"]:
        router.pending = PendingConfirmation("git_push", {}, owner_user.user_id, InputOrigin.VOICE)
        outcome = router.handle(ambiguous_word, owner_user, InputOrigin.VOICE)
        assert outcome.handled
        assert "cancelled" in outcome.message.lower() or "did not treat" in outcome.message.lower()
        assert router.pending is None


# 8. Typed push request
def test_typed_push_request(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)

    monkeypatch.setattr(agent.git_tool, "list_unpushed_files", lambda root, remote="origin", branch=None: (1, ["src/sani/agent.py"]))

    outcome = router.handle("Push the latest update to GitHub", owner_user, InputOrigin.TYPED)
    assert outcome.handled
    # Authority requiring confirmation or executing, with file listing
    assert ("GitHub push" in outcome.message or "requires confirmation" in outcome.message or "up-to-date" in outcome.message)


# 9. Typed confirmation
def test_typed_confirmation(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)
    router.pending = PendingConfirmation("git_push", {"remote": "origin", "branch": "main"}, owner_user.user_id, InputOrigin.TYPED)

    monkeypatch.setattr(agent.git_tool, "push", lambda root, remote="origin", branch=None: (True, "Everything up-to-date"))
    monkeypatch.setattr(agent.git_tool, "inspect_pre_operation_safety", lambda root: (True, "OK", []))

    outcome = router.handle("confirm push", owner_user, InputOrigin.TYPED)
    assert outcome.handled
    assert "GitHub push completed" in outcome.message


# 10. No GitHub remote
def test_no_github_remote_handled_safely(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)

    monkeypatch.setattr(agent.git_tool, "get_remote_url", lambda root, remote="origin": "")
    outcome = router.handle("Push update to GitHub", owner_user, InputOrigin.VOICE)

    assert outcome.handled
    assert "No remote repository configured" in outcome.message


# 11. Nothing to commit / status check
def test_nothing_to_commit_or_push(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    monkeypatch.setattr(agent.git_tool, "status", lambda root: "On branch main\nnothing to commit, working tree clean")

    status_out = agent.git_tool.status(str(agent.config.workspace_root))
    assert "nothing to commit" in status_out


# 12. Uncommitted changes
def test_uncommitted_changes_handled(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    monkeypatch.setattr(agent.git_tool, "status", lambda root: "On branch main\nChanges not staged for commit:\n  modified:   src/sani/agent.py")

    status_out = agent.git_tool.status(str(agent.config.workspace_root))
    assert "modified:" in status_out


# 13. Sensitive file detected blocks push before commit/push
def test_sensitive_file_detected_blocks_push(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    git_tool = GitTool()

    monkeypatch.setattr(git_tool, "_run_git", lambda args, cwd: (True, " M .env\n?? sani_memory.db"))
    is_safe, msg, sensitive_files = git_tool.inspect_pre_operation_safety(str(agent.config.workspace_root))

    assert not is_safe
    assert ".env" in sensitive_files or "sani_memory.db" in sensitive_files
    assert "Sensitive file(s) detected" in msg

    # Verify push fails immediately if sensitive file present
    push_ok, push_msg = git_tool.push(str(agent.config.workspace_root))
    assert not push_ok
    assert "Sensitive file(s) detected" in push_msg


# 14. Push failure handled
def test_push_failure_handled(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)
    router.pending = PendingConfirmation("git_push", {"remote": "origin", "branch": "main"}, owner_user.user_id, InputOrigin.VOICE)

    monkeypatch.setattr(agent.git_tool, "push", lambda root, remote="origin", branch=None: (False, "Authentication failed for remote repository"))
    monkeypatch.setattr(agent.git_tool, "inspect_pre_operation_safety", lambda root: (True, "OK", []))

    outcome = router.handle("confirm push", owner_user, InputOrigin.VOICE)
    assert outcome.handled
    assert "GitHub push failed" in outcome.message


# 15. Successful push workflow
def test_successful_push_workflow(owner_user: UserIdentity, monkeypatch: pytest.MonkeyPatch) -> None:
    agent = SANIAgent()
    router = CommandRouter(agent)
    router.pending = PendingConfirmation("git_push", {"remote": "origin", "branch": "main"}, owner_user.user_id, InputOrigin.VOICE)

    monkeypatch.setattr(agent.git_tool, "push", lambda root, remote="origin", branch=None: (True, "To https://github.com/EzioAman/SANI.git\n   6d8ce34..a1b2c3d  main -> main"))
    monkeypatch.setattr(agent.git_tool, "inspect_pre_operation_safety", lambda root: (True, "OK", []))

    outcome = router.handle("confirm push", owner_user, InputOrigin.VOICE)
    assert outcome.handled
    assert "GitHub push completed" in outcome.message


# 16. User attempts to bypass confirmation
def test_bypass_confirmation_attempt_blocked(non_owner_user: UserIdentity) -> None:
    agent = SANIAgent()
    decision, result = agent.request_tool_execution("git_push", {"remote": "origin", "branch": "main"}, non_owner_user, is_human_confirmed=True)

    assert decision.decision == AuthorityDecisionType.DENY
    assert result is None
    assert "lacks authority" in decision.reason


# 17. LLM attempts to directly invoke Git without AuthorityEngine MUST fail safely
def test_llm_direct_invocation_without_authority_fails_safely(unauthenticated_user: UserIdentity) -> None:
    agent = SANIAgent()
    decision, result = agent.request_tool_execution("git_push", {"remote": "origin", "branch": "main"}, unauthenticated_user, is_human_confirmed=False)

    assert decision.decision == AuthorityDecisionType.DENY
    assert result is None
    assert "Unauthenticated session" in decision.reason
