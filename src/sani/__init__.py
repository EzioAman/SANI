"""SANI Initialization Package & Entrypoint."""

import sys
from sani.agent import SANIAgent
from sani.config import get_config
from sani.memory.sqlite_store import SQLiteMemoryStore
from sani.models import Role, UserIdentity
from sani.providers.llm_provider import GeminiProvider
from sani.voice.pipeline import VoicePipeline


def main() -> None:
    """SANI Main Entrypoint."""
    config = get_config()
    
    # Initialize SQLite Memory Store & Core Agent
    memory_store = SQLiteMemoryStore()
    agent = SANIAgent(memory_provider=memory_store)

    provider_name = "Google Gemini" if isinstance(agent.llm_provider, GeminiProvider) else "OpenAI"
    key_status = "CONFIGURED (via .env / environment)" if (config.gemini_api_key or config.openai_api_key) else "NOT SET"

    print(f"==================================================")
    print(f"  SANI Core Agent Baseline v0.1.0")
    print(f"  Primary Owner:    {config.owner_name}")
    print(f"  Workspace Root:   {config.workspace_root}")
    print(f"  Database Path:    {config.db_path}")
    print(f"  Active Model:     {provider_name}")
    print(f"  API Key Status:   {key_status}")
    print(f"==================================================")

    # Primary Owner Identity
    aman_identity = UserIdentity(
        user_id="aman_01",
        name=config.owner_name,
        role=Role.OWNER,
        is_authenticated=True,
    )

    # Check CLI args for --voice flag
    if "--voice" in sys.argv or "-v" in sys.argv:
        pipeline = VoicePipeline(agent=agent)
        pipeline.run_continuous_loop(aman_identity)
        return

    print(f"\nSANI ready for owner '{aman_identity.name}'.")
    print("Type your message to test text interaction, or type '/voice' for Voice Mode, or 'exit' / 'quit' to stop.\n")

    if not sys.stdin.isatty():
        # Non-interactive test run
        response = agent.chat("Hello SANI, introduce yourself.", user=aman_identity)
        print(f"SANI > {response}")
        return

    while True:
        try:
            user_input = input(f"{aman_identity.name} > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Shutting down SANI session. Goodbye!")
                break
            if user_input.lower() == "/voice":
                pipeline = VoicePipeline(agent=agent)
                pipeline.run_continuous_loop(aman_identity)
                print("\nExited Voice Mode. Back to text prompt.")
                continue

            response = agent.chat(user_input, user=aman_identity)
            print(f"SANI > {response}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break


if __name__ == "__main__":
    main()
