# The Workflow

Three stages: pre-project conversation and research, project scaffolding, active development. Plus long-term maintenance once a project has run for a while.

## Stage 1: Pre-project conversation and research

Before any code or project folder exists, you talk to the agent about what you want to build.

### 1a. Initial conversation

Start a Codex or Claude Code session in any folder. Describe the software you want to build. Let the agent ask probing questions:

- What is it? Who uses it?
- What problem does it solve?
- What's the tech stack and target platform?
- What are the hard performance, latency, or quality requirements?
- What's the scale: prototype, hobby project, production system?
- What's the licensing model and distribution path?

Don't rush this. The conversation produces the context for everything that follows. Aim for 30 to 90 minutes of back and forth before moving on.

### 1b. Research prompts

When you've discussed the broad shape, invoke `/research-prompt`. The agent writes a structured investigation document to `docs/research_prompts/<topic-slug>.md`. The document contains questions only, no answers.

You'll usually need 2 to 5 research prompts:
- Architecture (how do production systems handle this?)
- Performance and scale (real bottlenecks at the target size?)
- Tooling and library choices (build vs borrow trade-offs)
- Domain-specific concerns (graphics pipeline, model deployment, network protocol, etc.)

### 1c. External deep research

Paste each research prompt into Google Gemini Deep Research, ChatGPT Deep Research, or your preferred deep research tool. Each prompt runs for 5 to 15 minutes and produces a long markdown document with cited findings.

Save each result as `docs/research_results/<topic-slug>.md`.

### 1d. Discuss findings

Bring the research results back to the agent. Discuss findings, identify open questions, refine the architectural direction. Iterate. If new questions emerge, write more research prompts and run them.

By the end of Stage 1, you should know: the architecture, the tech stack, the major risks, and the rough phasing of the work.

### 1e. Spec draft (multi-week projects)

For multi-week projects with non-trivial architecture risk, invoke `/spec-draft` to produce `docs/design/spec.md` from the research and conversation. The spec captures every load-bearing decision, every Pick + Why Not Alternatives, every Risk, every Open Question. It becomes the authority that `/audit` measures work against.

Two modes: full (Sentinel-2 style, 15+ sections, deep technical detail) and lite (8-10 sections, scoped 2-3 week projects). Skip entirely for prototypes and throwaway scripts.

## Stage 2: Scaffold the project

Once you have a clear direction (and optionally a spec), invoke `/scaffold-project`. The agent asks for:

- Project name and parent directory
- Tech stack
- Major architectural components
- Design principles
- Initial skills the agent will need
- Any existing research to copy in
- Whether to scaffold MCP co-development infrastructure
- Relevant playbooks from the global library to surface

The agent builds the full project: `AGENTS.md`, a Claude Code compatibility `CLAUDE.md`, `docs/SCHEMA.md` (frontmatter contract), `docs/implementation-plan.md`, phase docs with frontmatter, knowledge base index, `docs/state.md`, `docs/lessons.md`, code skeleton, `.gitignore`, git init, optional GitHub publish.

If a `docs/design/spec.md` exists from `/spec-draft`, the implementation plan derives from it.

### MCP co-development for non-web apps

If your project is a native, desktop, graphics, AI, or CLI application, the scaffold skill recommends MCP co-development. This means building a small Rust MCP server alongside your app from day one, so the agent can test and verify features as they ship.

Read the playbook at the active agent playbook path, usually `~/.agents/playbooks/mcp-co-development.md`. The architecture in one paragraph: a Rust MCP server (~2MB static binary) talks to your app over ZeroMQ REQ/REP with JSON. The app exposes a state tree (path-addressed parameter registry), an IPC bridge (command queue with main-thread safety), and a capture system (screenshots and texture readback). The MCP server provides ~7 multi-action tools. The agent uses this surface to verify every feature end-to-end as it ships.

For pure web apps, skip MCP co-development. Browser DevTools and web-fetching tools usually give the agent enough visibility.

## Stage 3: Active development

Open Codex or Claude Code in the new project folder.

### `/formalize-plan` (after plan mode)

After plan-mode planning, formalize the plan into project docs. Writes `docs/phases/phase-{N}-{slug}.md` with proper frontmatter, updates `docs/implementation-plan.md` Phase Overview table, updates `AGENTS.md` and `CLAUDE.md` Current Status. Commits as `docs(plan): Phase N - Title`.

### `/plan-audit` (optional, before starting a new phase)

For phases that involve new libraries, multi-week effort, or architectural commitments, run `/plan-audit` after `/formalize-plan` and before `/start-session`. Three parallel Explore agents check:
- Spec alignment: does the plan deliver what the spec / research says is needed?
- Toolchain feasibility: do the libraries / APIs exist and behave as the plan assumes?
- Sub-phase decomposition: are sub-phases independently verifiable, dependencies explicit?

Applies a best-guess fix to the plan doc for every finding it can — derived fixes (missing pass criteria, unnamed dependencies, corrected version assumptions, mega-phase splits) and judgement calls (dropping an untraceable deliverable, picking a replacement library, covering a spec gap) alike — then reports what it changed, flagging the judgement calls with the alternative so you can revert any in one step. Only genuinely-unguessable findings are left as open questions. Skip for routine sub-phases.

### `/slash-goal` (optional, to run a phase autonomously)

After `/formalize-plan` (and optional `/plan-audit`), if you want one or more phases to run under Claude Code's built-in `"slash goal"` loop instead of driving each sub-phase by hand, run `/slash-goal`. It reads the formalized phase doc(s) and emits a single **completion-condition string** to paste into the `"slash goal"` command (Claude Code v2.1.139+).

The goal is a **thin pointer**, not a wall of text. The phase doc is the contract: `/formalize-plan` writes it with per-sub-phase pass criteria and an **Autonomy & human-in-the-loop** section that marks where a person is genuinely needed (batched so autonomous stretches stay long) and classifies each pause into one of three gate tiers — **self-serve** (aesthetic/visual checks and the per-sub-phase approval cadence → run the check, log the verdict + screenshot, commit `approval: pending`, continue), **conditional-proceed** (a real decision pre-authorized with a testable rule — "accept the dep if `cargo deny` passes and the license is MIT/Apache, else stop"), and **hard-stop** (the genuinely irreversible or unsettled — git history rewrite, spec edits, a core/upstream fork, a failed pre-authorized condition, an unsettled decision). The human's judgment is spent once, at plan time.

The generated goal then just names the phase, points at its doc, and sets the standing rails: `$start-session` to open, proof-first per the doc, a per-slice `$audit`, close-out via `$end-session`, explicit-paths-only / no `git add -A` / no push, an anti-stall clause so a permission prompt can't freeze the loop, "don't start the next phase," and "stop only for the doc's hard blockers." Because the `"slash goal"` evaluator only judges what's surfaced in the transcript, the doc's proof method must produce transcript-visible evidence. Workflow commands use a `$` prefix (Codex-style), not a slash. The skill returns the goal inline in chat (never a file); you run the command. `/formalize-plan` offers `/slash-goal` as the next step once the Autonomy section is in place.

### `/start-session`

Begin a session. The agent reads the last commit, the most recent devlog's `approval` frontmatter (knows immediately whether to start the next phase or resume), `docs/state.md` for current focus, and audits the next planned task for completeness. If anything is unplanned or vague, plan first.

### `/checkpoint`

Save progress mid-work. Writes a devlog entry, commits, and explicitly does NOT mark anything approved. Use this when you're pausing partway through a sub-phase.

### `/wrap`

Lightweight sub-phase close-out — the middle weight between `/checkpoint` and `/end-session`. When a sub-slice meets its pass criterion and you want to roll straight to the next one, `/wrap` writes a short devlog (`status: complete`, `approval: pending`) and commits the touched paths, then stops. It deliberately skips the `/end-session` ceremony (lessons, schema audit, slim/playbook nudges, state.md walk, plan verification, Current Status changes) — those happen at the real phase boundary. The per-slice closer that `/slash-goal` goals reference: `$wrap` each slice, a full `$end-session` at phase end. If a slice actually finishes a whole phase, use `/end-session` instead so the boundary is recorded.

### `/audit`

Quality gate at any point in a session. Three parallel Explore agents (code, spec, test). If `docs/design/spec.md` exists, the spec agent measures against it by section number. Includes phase coherence check (do changes match active phase doc scope) and missing-devlog detection.

Applies safe fixes (small, mechanical), surfaces larger issues for your decision.

### `/end-session`

Multi-phase wrap-up:
1. Read context (last devlog, state.md, git status)
2. Close the devlog (frontmatter `status: complete`, `session_end`, `approval`)
3. Phase approval check (flip frontmatter, update AGENTS.md and CLAUDE.md Current Status)
4. Update `docs/state.md`
5. Lessons prompt (any sneaky bugs? → append to `docs/lessons.md`)
6. Schema audit (validate frontmatter on touched files)
7. Slim suggestion (if AGENTS.md or CLAUDE.md crossed 25K chars)
8. Playbook nudge (every 5th approved phase, configurable)
9. Verify implementation plan was updated
10. Commit

### `/find-session`

Find and inspect previous agent session transcripts where supported. Useful when you want to recall what happened in a session days ago.

## The shape of a good session

1. `/start-session` runs. The agent reviews last commit, reads state.md, checks devlog frontmatter, audits next task, starts work.
2. The agent implements, tests, fixes. It iterates with you when decisions are needed.
3. Optional: `/audit` mid-session if the work is touching sensitive code.
4. Optional: `/checkpoint` if pausing without finishing the sub-phase.
5. `/end-session` runs. Walks the 10 phases, commits.

The discipline:
- Every commit is preceded by a closed devlog.
- Every phase boundary is explicitly marked via frontmatter `approval: approved`.
- `AGENTS.md` and `CLAUDE.md` Current Status reflect where you actually are (1-3 lines). Detail lives in `docs/state.md`.
- Sneaky bugs go to `docs/lessons.md` so future-you doesn't re-derive them.
- Significant cross-project patterns get extracted via `/extract-playbook`.

## Long-term maintenance

After many sessions, several things drift if untended.

### Agent instructions grow

Detail accretes. Known Pitfalls collections grow, Current Status turns into a series of mini-devlogs, individual subsystems get multi-page sections. Past 25,000 characters, session startup slows. Past 40,000, agent context gets crowded.

When `AGENTS.md` or `CLAUDE.md` crosses 25,000 characters, run the slimming workflow. The skill walks every section, classifies each as keep, compress, extract to a knowledge file, extract to lessons.md (for pitfall-shaped content), extract to a new skill, or delete (only when stale or duplicated). Shows the plan before applying. Hard ceiling 40K chars, target 20-25K.

### Cross-project patterns recur

When you're working in project B and recognize a pattern you already solved in project A, run `/extract-playbook`. The skill scans the current project's agent instruction files and `docs/knowledge/` for cross-project-shaped content and proposes playbook drafts. Approved playbooks land in the active global playbook library and become available across all future projects.

`/end-session` nudges this every 5 approved phases ("anything from recent work worth extracting?"). Configurable via `playbook_nudge_every` in the active agent settings file. Set to 0 to disable.

### Playbooks age

Quarterly, run `/audit-playbooks`. Quick mode flags entries past `last_verified` threshold (default 90 days). Deep mode spawns Explore agents to spot-check claims against current library docs. Surfaces what needs refreshing; you decide what to update.

## When the workflow shines

This workflow earns its keep on projects that span weeks or months and involve architectural decisions you can't reverse cheaply. The research-first approach keeps you from picking the wrong foundation. The spec phase locks decisions in writing before code is committed. Plan-audit catches plan-level issues while they're cheap. Session commands keep context coherent across many sittings. The MCP co-development pattern (for non-web apps) means the agent can verify the work end-to-end. Cross-project playbooks compound across all your work.

For a one-day script or a throwaway prototype, the overhead is too high. Skip the bundle and just talk to the agent.
