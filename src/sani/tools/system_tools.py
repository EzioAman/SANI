"""System & Publishing Tools for SANI Agent Introspection and Git Operations."""

from typing import TYPE_CHECKING
from sani.config import get_config
from sani.models import ActionRiskLevel

if TYPE_CHECKING:
    from sani.agent import SANIAgent


def inspect_system_tools(agent: "SANIAgent") -> str:
    """Return a human-readable list of all tools registered in SANI."""
    tools = agent.tool_registry.list_tools()
    if not tools:
        return "No tools currently registered."

    output = "Registered SANI Tools:\n" + "=" * 45 + "\n"
    for tool in tools:
        output += f"• Name:        {tool.name}\n"
        output += f"  Risk Level:  {tool.risk_level.value}\n"
        output += f"  Description: {tool.description}\n\n"
    return output.strip()


def inspect_system_status(agent: "SANIAgent") -> str:
    """Return detailed health and configuration status of SANI components."""
    config = get_config()
    workspace = str(config.workspace_root)
    branch = agent.git_tool.get_current_branch(workspace) or "detached HEAD"
    remote = agent.git_tool.get_remote_url(workspace) or "None configured"
    commit = agent.git_tool.get_commit_log(workspace, count=1) or "No commits"

    llm_name = agent.llm_provider.__class__.__name__

    output = (
        f"SANI System Status:\n"
        f"=============================================\n"
        f"  • Primary Owner:    {config.owner_name}\n"
        f"  • LLM Provider:     {llm_name}\n"
        f"  • Workspace Root:   {workspace}\n"
        f"  • Database Path:    {config.db_path}\n"
        f"  • Active Branch:    {branch}\n"
        f"  • Git Remote:       {remote}\n"
        f"  • Recent Commit:    {commit}\n"
        f"  • Registered Tools: {len(agent.tool_registry.list_tools())}\n"
        f"============================================="
    )
    return output


def git_set_remote(agent: "SANIAgent", remote_url: str, remote_name: str = "origin") -> str:
    """Set or update the Git remote URL for publishing."""
    workspace = str(agent.config.workspace_root)
    ok, message = agent.git_tool.set_remote_url(workspace, remote_url=remote_url, remote_name=remote_name)
    return message


def git_publish(agent: "SANIAgent", remote_url: str | None = None) -> str:
    """Execute full project publish flow: configure remote (if provided), scan for secrets, open GUI review, push."""
    workspace = str(agent.config.workspace_root)

    # 1. Optionally set remote if provided
    if remote_url and remote_url.strip():
        ok, msg = agent.git_tool.set_remote_url(workspace, remote_url=remote_url.strip())
        if not ok:
            return f"Failed to set remote URL: {msg}"

    # 2. Check if remote is configured
    current_remote = agent.git_tool.get_remote_url(workspace)
    if not current_remote:
        return "Cannot publish: No Git remote configured. Provide a remote URL (e.g., https://github.com/user/repo.git)."

    # 3. Launch interactive PushWorkflowEngine
    from sani.tools.push_workflow import PushWorkflowEngine
    engine = PushWorkflowEngine(agent.git_tool, workspace)
    ok, result_msg = engine.run_interactive()
    return result_msg
