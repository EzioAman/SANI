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
from typing import Any
from sani.authority import AuthorityEngine
from sani.config import get_config
from sani.models import (
    ActionRiskLevel,
    AuthorityDecision,
    Role,
    ToolRequest,
    UserIdentity,
)
from sani.providers.llm_provider import GeminiProvider, LLMProvider, OpenAIProvider
from sani.providers.memory_provider import MemoryProvider
from sani.providers.voice_provider import DefaultVoiceProvider, VoiceProvider
from sani.tools.filesystem import generate_diff, list_directory, read_file, write_file
from sani.tools.registry import ToolRegistry
from sani.tools.runner import ToolRunner
from sani.tools.terminal import execute_terminal_command


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
            gemini_key = self.config.gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            openai_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")

            # Check if key is provided in GEMINI_API_KEY, GOOGLE_API_KEY, or OPENAI_API_KEY
            if gemini_key:
                self.llm_provider = GeminiProvider(api_key=gemini_key, model=self.config.model_name)
            elif openai_key and not openai_key.startswith("sk-"):
                # User placed a Gemini key in OPENAI_API_KEY variable
                self.llm_provider = GeminiProvider(api_key=openai_key, model=self.config.model_name)
            else:
                self.llm_provider = OpenAIProvider(api_key=openai_key or "", model="gpt-4o")


        self.voice_provider = voice_provider or DefaultVoiceProvider()
        self.memory_provider = memory_provider

        # Subsystems
        self.authority_engine = AuthorityEngine()
        self.tool_registry = ToolRegistry()
        self._register_default_tools()
        self.tool_runner = ToolRunner(self.tool_registry)

    def _register_default_tools(self) -> None:
        """Register built-in system tools with explicit risk levels."""
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

    def chat(self, prompt: str, user: UserIdentity) -> str:
        """Process conversational user prompt and return model response."""
        system_prompt = (
            f"You are SANI, a persistent personal AI agent. "
            f"Active User: '{user.name}' (Role: {user.role.value}). "
            f"Primary Authority: '{self.config.owner_name}'."
        )

        # Inject context memories if available
        if self.memory_provider:
            memories = self.memory_provider.search_memories(owner_id=user.user_id)
            if memories:
                memory_ctx = "\n".join([f"- [{m.memory_type}] {m.content}" for m in memories[:5]])
                system_prompt += f"\n\nRelevant User Memories:\n{memory_ctx}"

        return self.llm_provider.generate_response(prompt=prompt, system_prompt=system_prompt)

    def request_tool_execution(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user: UserIdentity,
        is_human_confirmed: bool = False,
    ) -> tuple[AuthorityDecision, Any | None]:
        """Request tool execution passing strictly through AuthorityEngine and ToolRunner."""
        tool_def = self.tool_registry.get_tool(tool_name)
        if not tool_def:
            raise ValueError(f"Unknown tool requested: '{tool_name}'")

        request = ToolRequest(
            tool_name=tool_name,
            arguments=arguments,
            requested_by=user,
        )

        # Step 1: Decision by AuthorityEngine (No execution)
        decision = self.authority_engine.evaluate(request, tool_def.risk_level)

        # Step 2: Execution by ToolRunner ONLY if decision permits
        result = None
        if decision.is_executable or (decision.decision.value == "REQUIRES_CONFIRMATION" and is_human_confirmed):
            result = self.tool_runner.execute(request, decision, is_human_confirmed=is_human_confirmed)

        return decision, result
