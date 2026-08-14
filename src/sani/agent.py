"""SANI Core Agent Orchestrator.

Integrates the 10 Core Architectural Commandments:
1. AuthorityEngine decides; it never executes.
2. ToolRunner executes; it never decides authority.
3. Tools independently validate parameters.
4. LLM requests actions but cannot bypass AuthorityEngine.
5. Confirmation happens outside model authority.
6. Replaceable LLMProvider (OpenAI, Gemini, Local models).
7. Replaceable VoiceProvider.
8. Replaceable MemoryProvider.
9. High-risk operations have deterministic controls.
10. Explicit Policy Conflicts (DENY vs POLICY_CONFLICT).
"""

import os
from typing import Any, Iterator
from sani.authority import AuthorityEngine
from sani.config import get_config
from sani.models import (
    ActionRiskLevel,
    AuthorityDecision,
    Role,
    ToolRequest,
    InputOrigin,
    UserIdentity,
)
from sani.providers.llm_provider import GeminiProvider, LLMProvider, OpenAIProvider
from sani.providers.memory_provider import MemoryProvider
from sani.providers.voice_provider import DefaultVoiceProvider, VoiceProvider
from sani.tools.filesystem import generate_diff, list_directory, read_file, write_file
from sani.tools.registry import ToolRegistry
from sani.tools.runner import ToolRunner
from sani.tools.terminal import execute_terminal_command
from sani.tools.git_tool import GitTool


class SANIAgent:
    """Core Agent Orchestrator for SANI."""

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        voice_provider: VoiceProvider | None = None,
        memory_provider: MemoryProvider | None = None,
    ) -> None:
        self.config = get_config()

        # Select model provider dynamically
        if llm_provider is not None:
            self.llm_provider = llm_provider
        else:
            api_key = (
                self.config.llm_api_key
                or os.getenv("LLM_API_KEY")
                or self.config.gemini_api_key
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
                or self.config.openai_api_key
                or os.getenv("OPENAI_API_KEY")
                or ""
            )

            if api_key.startswith("sk-"):
                self.llm_provider = OpenAIProvider(api_key=api_key, model="gpt-4o")
            else:
                self.llm_provider = GeminiProvider(api_key=api_key, model=self.config.model_name)


        self.voice_provider = voice_provider or DefaultVoiceProvider()
        self.memory_provider = memory_provider

        # Subsystems
        self.authority_engine = AuthorityEngine()
        self.tool_registry = ToolRegistry()
        self.git_tool = GitTool()
        self._register_default_tools()
        self.tool_runner = ToolRunner(self.tool_registry)

    def _register_default_tools(self) -> None:
        """Register built-in system tools with explicit risk levels."""
        from sani.tools.system_tools import (
            git_publish,
            git_set_remote,
            inspect_system_status,
            inspect_system_tools,
        )

        self.tool_registry.register(
            name="git_push",
            description="Push the checked-out branch to the configured Git remote.",
            risk_level=ActionRiskLevel.SYSTEM_CHANGING,
            func=lambda remote="origin", branch=None: self.git_tool.push(str(self.config.workspace_root), remote, branch),
        )
        self.tool_registry.register(
            name="git_publish",
            description="Publish the project to GitHub (sets remote if provided, security scans, opens interactive review window, stages, commits, and pushes).",
            risk_level=ActionRiskLevel.DESTRUCTIVE,
            func=lambda remote_url=None: git_publish(self, remote_url=remote_url),
        )
        self.tool_registry.register(
            name="git_set_remote",
            description="Set or update the Git remote URL for GitHub publishing.",
            risk_level=ActionRiskLevel.SYSTEM_CHANGING,
            func=lambda remote_url, remote_name="origin": git_set_remote(self, remote_url, remote_name),
        )
        self.tool_registry.register(
            name="inspect_system_tools",
            description="Inspect all tools registered in SANI with their descriptions, parameters, and risk levels.",
            risk_level=ActionRiskLevel.INFORMATIONAL,
            func=lambda: inspect_system_tools(self),
        )
        self.tool_registry.register(
            name="inspect_system_status",
            description="Inspect SANI system health, active LLM model, database status, workspace root, and Git remote configuration.",
            risk_level=ActionRiskLevel.INFORMATIONAL,
            func=lambda: inspect_system_status(self),
        )
        self.tool_registry.register(
            name="read_file",
            description="Read text file contents within workspace.",
            risk_level=ActionRiskLevel.INFORMATIONAL,
            func=read_file,
        )
        self.tool_registry.register(
            name="list_directory",
            description="List workspace directory contents.",
            risk_level=ActionRiskLevel.INFORMATIONAL,
            func=list_directory,
        )
        self.tool_registry.register(
            name="generate_diff",
            description="Preview file diff changes.",
            risk_level=ActionRiskLevel.INFORMATIONAL,
            func=generate_diff,
        )
        self.tool_registry.register(
            name="write_file",
            description="Write content to a workspace file.",
            risk_level=ActionRiskLevel.SYSTEM_CHANGING,
            func=write_file,
        )
        self.tool_registry.register(
            name="execute_terminal_command",
            description="Execute controlled shell command within workspace.",
            risk_level=ActionRiskLevel.DESTRUCTIVE,
            func=execute_terminal_command,
        )

    def _build_system_prompt(self, user: UserIdentity) -> str:
        base_prompt = (
            f"You are SANI, a personal AI assistant for {self.config.owner_name}. "
            f"Active User: '{user.name}' (Role: {user.role.value}).\n\n"
            f"ABSOLUTE RULES — NEVER BREAK THESE:\n"
            f"1. You are a CONVERSATIONAL assistant ONLY. You cannot push code, run commands, "
            f"edit files, stage commits, or perform ANY real-world action.\n"
            f"2. NEVER say 'I will push', 'I'm pushing', 'I've queued', 'I'm executing', "
            f"'initiating the sequence', or ANYTHING that implies you are performing an action. "
            f"You are NOT performing actions. You CANNOT perform actions.\n"
            f"3. NEVER mention internal system names like 'CommandRouter', 'AuthorityEngine', "
            f"'ToolRunner', 'pipeline', or 'execution engine' to the user. "
            f"The user does not need to know about internal architecture.\n"
            f"4. If asked to do something you cannot do (push code, run a command, edit a file), "
            f"say HONESTLY: 'I can't do that directly. Use the push command for that.' "
            f"Do NOT pretend or imply you are doing it.\n"
            f"5. If you don't know something, say 'I don't know.' Do NOT make up answers.\n"
            f"6. Keep responses natural, concise, and honest."
        )
        if self.memory_provider:
            memories = self.memory_provider.search_memories(owner_id=user.user_id)
            if memories:
                memory_ctx = "\n".join([f"- [{m.memory_type}] {m.content}" for m in memories[:5]])
                base_prompt += f"\n\nRelevant User Memories:\n{memory_ctx}"
        return base_prompt

    def chat(self, prompt: str, user: UserIdentity) -> str:
        """Process conversational user prompt and return model response."""
        system_prompt = self._build_system_prompt(user)
        return self.llm_provider.generate_response(prompt=prompt, system_prompt=system_prompt)

    def chat_stream(self, prompt: str, user: UserIdentity) -> Iterator[str]:
        """Yield actual provider response deltas for latency-sensitive interfaces."""
        system_prompt = self._build_system_prompt(user)
        yield from self.llm_provider.generate_response_stream(prompt, system_prompt)

    def request_tool_execution(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user: UserIdentity,
        is_human_confirmed: bool = False,
        origin: InputOrigin = InputOrigin.TYPED,
    ) -> tuple[AuthorityDecision, Any | None]:
        """Request tool execution passing strictly through AuthorityEngine and ToolRunner."""
        tool_def = self.tool_registry.get_tool(tool_name)
        if not tool_def:
            raise ValueError(f"Unknown tool requested: '{tool_name}'")

        request = ToolRequest(
            tool_name=tool_name,
            arguments=arguments,
            requested_by=user,
            origin=origin,
        )

        # Step 1: Decision by AuthorityEngine (No execution)
        decision = self.authority_engine.evaluate(request, tool_def.risk_level)

        # Step 2: Execution by ToolRunner ONLY if decision permits
        result = None
        if decision.is_executable or (decision.decision.value == "REQUIRES_CONFIRMATION" and is_human_confirmed):
            result = self.tool_runner.execute(request, decision, is_human_confirmed=is_human_confirmed)

        return decision, result
