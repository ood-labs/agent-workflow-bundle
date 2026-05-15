---
name: start-session
description: Start session - review last commit and get up to speed
allowed-tools: Read, Glob, Grep, Bash(git log:*), Bash(git show:*), Bash(git diff:*)
user-invocable: true
---

Look at the previous commit and see where we left off. Read everything you need to know to get up to speed.

CONTEXT TO READ AT START:
- Last commit (`git log -1`, `git show HEAD`) for what shipped most recently
- Most recent devlog in `docs/devlogs/` — check frontmatter `approval` field for `approved` vs `pending`. This drives PHASE TRANSITIONS below.
- `docs/state.md` if it exists — slim snapshot of current focus, blockers, decisions pending. Read this for orientation.
- `AGENTS.md` and/or `CLAUDE.md` Current Status section — high-level phase context.
- The current phase doc from `docs/phases/` (referenced in state.md or implementation-plan.md).

If the active instruction file's Current Status references a date older than ~2 weeks, surface it: "Current Status hasn't been updated in N days, may be stale." Don't auto-fix; let the user decide.

PLANNING AUDIT: Before starting any work, audit the next task for plan completeness. The next task should have a clear, written plan you can point to — a sub-phase entry in the implementation plan, a phase doc with pass criteria, or a saved plan file in the active agent plan directory (e.g. `~/.agents/plans/*.md`, `~/.codex/plans/*.md`, or `~/.claude/plans/*.md`). For each piece of upcoming work, verify:
- The scope is bounded (you know what is in and what is out)
- Pass criteria or definition-of-done is stated
- Dependencies and decisions are resolved (no open D-numbered questions blocking the work)
- Sub-phase decomposition exists if the work spans more than a single sitting

If anything is unplanned, vague, or has unresolved decisions, STOP and enter plan mode first. Draft a plan, surface the open questions, and align before coding. For multi-week or multi-sub-phase work, suggest the user run `/plan-audit` (three parallel Explore agents: spec-alignment / toolchain-feasibility / sub-phase decomposition). The pattern caught 15 plan-level issues on Spike 5 before any code was written. Only proceed to implementation once the plan is concrete.

IMPORTANT: Do NOT ask for confirmation before proceeding once the plan is clear. After the planning audit passes (or after we've aligned on a fresh plan), immediately start working on the next task without waiting for my approval.

TESTING: Always test what you build before considering it done. This means actually running or opening the app to verify it works - not just getting it to compile. If it's a UI change, open the app and check it visually. If it's a feature, exercise the feature end-to-end. Don't wait for me to ask "did you actually try it?" - proactively verify your work functions correctly.

TOOLING: If you're having trouble testing something programmatically, don't just rely on manual verification - create better automation tooling. Expose what you need through the IPC/AutomationBridge so you can test it properly. The StateTree should give you access to verify state, and actions should let you drive the app. If something isn't exposed yet, add it.

PACING: Work continuously through subtasks without stopping. When you complete a subphase (4a, 4b, 4b.5, etc.), stop for review. If a phase has no subphases, complete the whole phase before stopping. This is where the session ends and I'll run /end-session to approve it.

PHASE TRANSITIONS: Read the most recent devlog's frontmatter `approval` field:
- `approval: approved` → previous sub-phase / phase is signed off. Start the next one immediately. Don't ask for approval again.
- `approval: pending` → work was in progress when the last session ended. Resume where it left off; don't treat it as a fresh start.

Only stop for approval when YOU just finished a sub-phase / phase in THIS session. Approval happens during `/end-session`, not `/start-session`.

If the project predates the frontmatter contract and devlogs use the old text marker instead of frontmatter, fall back to grepping for the literal regex `\*\*Phase\s+\S+\s*/\s*Subphase\s+\S+:\s*APPROVED\*\*` (matches `**Phase 4b / Subphase 4b: APPROVED**` etc.). If the legacy marker is found in the most recent devlog body, treat it as `approval: approved`. Suggest the user adopt the frontmatter contract going forward (e.g., by running `/slim-agent-md` and applying the new format on the next devlog).
