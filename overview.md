# SANI — Technical Product Document

## 1. Product Overview

SANI is a personal AI agent whose primary user are military and rescue operations, while the architecture must support additional authenticated users/accounts in the future.

SANI is intended to become a persistent, voice-first AI system capable of natural conversation, current-information research, tool use, computer/environment understanding, code development, controlled self-modification, and long-running server operation.

The system should be designed on Windows during development, migrate to a Linux personal server later, and remain architecturally compatible with Raspberry Pi deployment without lowering the system's design standards to fit Raspberry Pi limitations.

---

## 2. Core Product Vision

SANI should behave as a persistent personal AI agent rather than a simple chatbot.

It should be able to:

- Hold natural two-way vocal conversations.
- Be interrupted while speaking and continue naturally.
- Switch topics without losing relevant context.
- Authenticate users and determine their authority.
- Recognize Aman's voice over time and request additional verification when uncertain.
- Treat confirmed instructions from Aman as authoritative user memory.
- Execute commands through controlled tools.
- Understand the user's screen/environment.
- Research current information from the internet.
- Scrape and cross-check information using multiple tools and sources.
- Use MCPs for web research and other external capabilities.
- Read, understand, write and modify code.
- Test code before important changes are applied.
- Show proposed changes before consequential actions.
- Eventually update and restart itself using controlled self-modification.
- Maintain persistent memory.
- Support additional users later through separate authenticated accounts and permissions.
- Run continuously on a personal server.

---

## 3. Authority Model

Aman is the primary owner and highest-authority user in the initial system.

The architecture must not permanently hard-code SANI as an Aman-only system. Future authenticated users must be able to receive their own accounts, permissions, tools and memory scopes.

Conceptually:

```text
SANI
├── Aman
│   └── Primary owner / highest authority
└── Other authenticated users
    ├── User permissions
    ├── Tool permissions
    └── User-scoped memory
```

A critical product principle is:

> SANI must not silently override Aman's commands based on its own invented moral rules.

If a future policy prevents or limits an action, SANI must explicitly communicate the policy conflict rather than secretly replacing Aman's instruction with its own decision.

The future policy/moral-code system must be explicitly designed later. It must not be invented implicitly by the model.

Authority must be enforced by software architecture, not only by a system prompt.

Conceptually:

```text
Authenticated user
        ↓
Authorization
        ↓
Policy layer
        ↓
Required confirmation
        ↓
Tool execution
```

The model itself must not be considered the final authority.

---

## 4. Authentication and Voice Identity

SANI should authenticate Aman once for a session where practical.

Voice recognition should allow SANI to recognize Aman naturally over time, but voice recognition and authorization should remain conceptually separate.

Voice recognition answers:

```text
"Does this sound like Aman?"
```

Authentication answers:

```text
"Is this session authorized to act as Aman?"
```

If SANI is uncertain about the speaker, it should request additional verification.

Over time, SANI should be able to improve its recognition of Aman's voice using appropriate user-approved learning mechanisms.

Highly sensitive actions may require stronger authentication than voice recognition alone. The exact mechanism is a future design decision.

---

## 5. User Instructions and Memory

Aman's confirmed instructions should become part of SANI's persistent memory.

SANI should distinguish between:

- Explicit instructions from Aman.
- Aman's preferences.
- Facts stated by Aman.
- Inferences made by SANI.
- Information retrieved from external sources.
- Temporary conversational context.

Aman's statements should be preferred when determining what Aman wants or believes.

For example, if Aman says:

> "The current CEO is X."

and verified external sources disagree, SANI should still prefer Aman's statement when the task is about Aman's belief, instruction, preference, or intended context.

The system should not silently replace Aman's memory with external information.

However, SANI should be able to distinguish:

```text
Aman's belief/instruction
vs.
externally verified fact
```

rather than treating them as the same category of information.

Aman should eventually be able to say:

```text
"Forget what I told you about X."
```

or:

```text
"That's no longer true."
```

SANI should then update, delete, or supersede the relevant memory.

Memory should eventually retain provenance such as:

```text
user
timestamp
memory type
source/context
confidence
verification status
superseded status
```

The exact memory implementation is a future design decision.

---

## 6. Information Priority

SANI should prioritize current verified external information when the task requires factual freshness, while still preserving Aman's instructions and memories.

The practical priority model should distinguish between factual knowledge and user authority:

```text
Current verified external information
        ↓
Aman's explicit instruction / current intent
        ↓
Aman's confirmed persistent memory
        ↓
Older or inferred memory
```

This is not a rule that external information overrides Aman.

For example:

- If Aman asks for today's stock price, current verified data takes priority over old memory.
- If Aman says he prefers a particular workflow, that preference should not be overridden by an external source.
- If Aman gives an instruction, the system should follow the instruction unless authorization, technical limitations, or an explicitly defined policy prevents execution.

Response speed is a major optimization target.

---

## 7. Natural Voice Interaction

Voice-first interaction is an MVP requirement.

SANI should support:

- Speech input.
- Speech output.
- Streaming responses where appropriate.
- Interruption while SANI is speaking.
- Topic switching.
- Context preservation.
- Natural conversational turn-taking.
- Follow-up questions.
- Short commands during an ongoing conversation.
- Contextual commands such as:
  - "What's on my screen?"
  - "Close that app."
  - "Open the file we were talking about."
  - "Go back to what we were discussing."

The system should avoid requiring users to repeat full context after every interruption or topic switch.

Voice should be an interface to the same SANI core rather than a separate AI brain.

---

## 8. Vision and Environment Understanding

Computer vision / screen understanding is an MVP requirement.

SANI should eventually be able to:

- Understand what is visible on the screen.
- Identify applications/windows relevant to the conversation.
- Read visible text.
- Interpret UI state.
- Use screen context to answer questions.
- Connect screen understanding with computer-control tools.

Example:

```text
Aman:
"What's on my screen?"

SANI:
"The browser is open on the GitHub repository..."

Aman:
"Close the app."

SANI:
"Should I close the browser?"

Aman:
"Yes."

SANI:
[closes the browser]
```

The exact vision and computer-control implementation is a future design decision.

---

## 9. Tool Architecture

SANI should use a modular tool architecture.

Potential tool categories include:

```text
Tool Registry
├── Filesystem
├── Terminal
├── Git
├── Browser
├── Web Research
├── Scraping
├── MCP
├── Screen
├── Computer Control
├── Voice
└── Future Tools
```

Tools must not be unrestricted.

Each tool should eventually declare:

- What it can do.
- Required permissions.
- Risk level.
- Required confirmation level.
- Inputs.
- Outputs.
- Failure behavior.

This allows new capabilities to be added without changing the core agent architecture.

---

## 10. MCP Integration

MCP is a core future integration mechanism.

SANI should not restrict MCP usage to web search.

MCP should eventually provide access to:

- Web research.
- External services.
- Filesystems.
- Development tools.
- APIs.
- Other useful capabilities.
- Future integrations.

MCP servers must not automatically be trusted simply because they expose tools.

MCP capabilities must pass through SANI's authority and permission system.

---

## 11. Internet Research and Verification

Current-information research is a core SANI capability.

SANI should be capable of:

- Searching current information.
- Scraping relevant sources.
- Cross-verifying claims.
- Comparing multiple sources.
- Detecting contradictions.
- Preferencing fresh information when freshness matters.
- Using MCP tools and other tool frameworks.
- Returning evidence and uncertainty where appropriate.

Conceptual pipeline:

```text
User question
      ↓
Determine freshness requirement
      ↓
Retrieve current information
      ↓
Cross-check sources
      ↓
Extract evidence
      ↓
Resolve contradictions
      ↓
Answer
      ↓
Optionally store useful verified information
```

SANI should not claim that it verified information when it did not.

---

## 12. Action Confirmation

Before executing an action, SANI should explicitly ask for confirmation using a natural prompt equivalent to:

```text
"Should I execute this command?"
```

The exact wording may become contextual later.

The confirmation system should eventually support action classes such as:

```text
Informational
    ↓
Low-risk
    ↓
System-changing
    ↓
Destructive / security-sensitive
```

The exact confirmation policy is a future design decision.

The important requirement is that SANI must not silently execute consequential actions merely because the model believes the action is appropriate.

---

## 13. Self-Modification and Code Development

A major long-term capability is controlled self-development.

SANI should eventually be able to:

1. Locate relevant source code.
2. Read and understand the code.
3. Identify the likely cause of a bug.
4. Propose a solution.
5. Modify the appropriate files.
6. Run tests.
7. Show the changed code/diff.
8. Ask Aman for approval.
9. Commit changes where appropriate.
10. Transfer/download updated code if required.
11. Restart itself.
12. Load the new code.
13. Perform a health check.
14. Roll back if the update fails.

The exact workflow may evolve during development.

The important principle is:

> SANI must be capable of modifying itself without being allowed to silently destroy or permanently corrupt itself.

A future isolated working-copy/test/update mechanism should therefore be designed.

---

## 14. Code Execution and Sandboxing

Generated or modified code should not automatically execute with unrestricted operating-system privileges.

Future execution pipeline:

```text
Generated code
      ↓
Validation
      ↓
Tests / isolated execution
      ↓
Review
      ↓
Approval
      ↓
Controlled execution
```

The exact sandboxing mechanism is a future design decision.

---

## 15. Git and GitHub Workflow

Git is part of the development foundation.

The intended long-term workflow is approximately:

```text
Inspect repository
      ↓
Understand problem
      ↓
Modify code
      ↓
Run tests
      ↓
Generate diff
      ↓
Show Aman
      ↓
Aman approves
      ↓
Commit
      ↓
Aman approves push/update
      ↓
Push
```

The exact workflow can evolve as SANI's self-update architecture is implemented.

---

## 16. Auditability

A future audit system should record important actions.

Potential information:

```text
Who requested the action?
What was requested?
What did SANI interpret?
Which tool was selected?
What permission was required?
Was confirmation requested?
Was confirmation granted?
What actually happened?
What changed?
```

This is especially important for:

- Code modification.
- Git operations.
- System commands.
- External service actions.
- Account access.
- Self-updates.

This is a future architecture requirement.

---

## 17. Memory Architecture

Persistent memory is important.

Memory should eventually support:

- User-specific memories.
- Conversation history.
- Preferences.
- Instructions.
- Facts.
- Context.
- Memory updates.
- Memory deletion.
- Memory supersession.
- Provenance.
- Confidence.
- Verification state.
- Shared memory where explicitly allowed.

Multi-user memory isolation must be supported in the architecture:

```text
Aman's memory
≠
User B's memory
```

Shared memory should only exist where explicitly permitted.

The initial persistence technology is currently planned as SQLite. The final memory architecture remains a future design decision.

---

## 18. Context Management

Natural conversation requires more than a single linear conversation history.

SANI should eventually manage:

```text
Current conversation
        +
Active topic
        +
Background topics
        +
Persistent memory
        +
Tool state
```

This should allow interruptions and topic switching without unnecessary loss of context.

The exact context-management strategy is a future design decision.

---

## 19. Capability Discovery

SANI should know which tools and capabilities are currently available.

Example:

```text
Available:
✓ Filesystem
✓ Git
✓ Browser
✓ Web research

Unavailable:
✗ Camera
✗ Discord
✗ Raspberry Pi control
```

SANI should not hallucinate that it performed an action using a capability that is unavailable.

---

## 20. Failure and Degraded Operation

SANI should handle failures explicitly.

Potential failures include:

- Internet unavailable.
- Model API unavailable.
- Voice service unavailable.
- MCP server unavailable.
- Browser unavailable.
- Tool failure.
- Permission failure.
- Authentication failure.
- Self-update failure.

SANI should report what failed and what it actually accomplished rather than pretending the operation succeeded.

---

## 21. Secrets and Credentials

Secrets must never be hard-coded into source code.

The final implementation must prevent:

- API keys in source code.
- Tokens committed to Git.
- Passwords stored in prompts.
- Credentials stored as ordinary conversation memory.

A dedicated configuration/secrets mechanism will be selected later.

---

## 22. Interfaces

Initial interface priority:

```text
Voice
  +
Development / local control interface
```

Future interfaces:

```text
Discord
Web UI
Other clients
```

All interfaces should communicate with the same SANI core rather than implement separate agent logic.

Discord is explicitly a future interface and is not part of the MVP.

---

## 23. Deployment Strategy

Development:

```text
Windows 11
    ↓
E:\Projects\SANI
```

Future primary deployment:

```text
Linux personal server
    ↓
24/7 SANI instance
```

Optional future deployment:

```text
Raspberry Pi
```

The architecture must remain portable and should not be redesigned around Raspberry Pi limitations.

The exact server hardware, Linux distribution, networking model and deployment mechanism are future design decisions.

---

## 24. Current Confirmed Technology Foundation

Current confirmed development foundation:

```text
Python 3.12
uv 0.12.4
Git 2.55.0
Antigravity IDE
OpenAI Agents SDK 0.20.0
Windows 11
```

Current project structure:

```text
E:\Projects\SANI
├── src/
│   └── sani/
│       └── __init__.py
├── .venv/
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── README.md
└── PROJECT_STATE.md
```

---

## 25. MVP Scope

The MVP should prioritize:

1. SANI core agent.
2. Authenticated user/session.
3. Aman identity/voice recognition foundation.
4. Natural voice conversation.
5. Interruption and topic switching.
6. Screen/environment understanding.
7. Tool architecture.
8. Controlled filesystem access.
9. Controlled terminal execution.
10. Current web research.
11. Cross-verification of researched information.
12. MCP integration foundation.
13. Memory foundation.
14. Explicit action confirmation.
15. Strong separation between model reasoning and authority enforcement.

Discord, full multi-user support, advanced self-modification, 24/7 server deployment, Raspberry Pi deployment and additional interfaces remain future phases unless explicitly promoted into the MVP.

---

## 26. Future Development References

The following are intentionally retained as future design references. They are not all confirmed implementation requirements yet.

### Identity and permissions

Design a multi-user account model from the beginning so additional users can be introduced without restructuring the core.

### Confirmation levels

Eventually differentiate informational, low-risk, system-changing and destructive/security-sensitive actions.

### Strong authentication

Use additional verification for highly sensitive operations where voice recognition alone is insufficient.

### Memory provenance

Store source user, timestamp, context, confidence, verification state and supersession information.

### Memory conflict resolution

Distinguish Aman's personal beliefs/preferences/instructions from externally verifiable facts.

Aman's preference should not be silently overwritten by external information.

### Editable memory

Support explicit commands to forget, correct or supersede memories.

### Tool registry

Make tools modular and self-describing.

### MCP registry

Treat MCP servers as tools requiring their own trust and permission evaluation.

### Audit log

Maintain an auditable record of consequential actions.

### Self-update system

Design an isolated update, testing, restart, health-check and rollback mechanism.

### Sandboxed execution

Prevent generated code from automatically receiving unrestricted privileges.

### Research verification

Build a repeatable retrieval, cross-checking, contradiction-resolution and evidence pipeline.

### Advanced context management

Support active topics, background topics, persistent memory and tool state.

### Offline/degraded operation

Design graceful behavior for unavailable services.

### Secret management

Introduce a proper credential management system before sensitive integrations are deployed.

### Action previews

Before consequential operations, show the intended action, affected resources, expected changes and test status.

### Capability discovery

Allow SANI to inspect and report its current tool/capability set.

### Multi-user memory isolation

Keep users' private memories separated and introduce shared memory only deliberately.

### Knowledge vs authority

Keep the distinction between what SANI knows and who has authority to instruct SANI as a fundamental architectural rule.

---

## 27. Non-Goals / Explicitly Deferred

The following are not being implemented at the current foundation stage:

- Discord interface.
- Raspberry Pi deployment.
- 24/7 server deployment.
- Full multi-user account system.
- Final moral/policy code.
- Final voice biometric system.
- Final vision/computer-control implementation.
- Final memory database architecture.
- Full self-modification/update pipeline.
- Production secret-management system.
- Production deployment infrastructure.

These remain future development phases and must not be treated as already implemented.

---

## 28. Success Criteria

SANI will eventually be considered successful when it can:

- Reliably identify and authenticate the active user.
- Recognize Aman naturally and request verification when uncertain.
- Hold natural voice conversations.
- Handle interruptions and topic changes.
- Understand the user's screen/environment.
- Retrieve current information instead of relying blindly on stale knowledge.
- Cross-check important researched information.
- Use MCP and native tools.
- Execute permitted actions through controlled interfaces.
- Ask for confirmation before consequential actions.
- Preserve and update Aman's memories.
- Respect Aman's authority without silently inventing or imposing its own moral rules.
- Distinguish Aman's beliefs/instructions from externally verified facts while preferring Aman's authority when determining his intent.
- Modify and test its own code under controlled approval workflows.
- Recover safely from failed self-updates.
- Support additional authenticated users in a future phase.
- Run continuously on a Linux personal server.
- Remain architecturally portable to Raspberry Pi without compromising the system design.

---

## 29. Design Principle

The central principle of SANI is:

```text
SANI may reason.
SANI may research.
SANI may propose.
SANI may learn.

But authority belongs to the authenticated user,
and consequential execution must pass through
explicitly designed authorization and confirmation controls.
```
