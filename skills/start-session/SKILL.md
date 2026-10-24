---
name: start-session
description: Start session - review last commit and get up to speed
allowed-tools: Read, Glob, Grep, Bash(git log:*), Bash(git show:*), Bash(git diff:*), Bash(git fetch:*), Bash(git status:*), Bash(python tools/workspace_check.py:*), Bash(bd:*)
user-invocable: true
---

Look at the previous commit and see where we left off. Read everything you need to know to get up to speed.

FETCH AND CHECK FIRST: run `git fetch origin` (read-only) so `origin/main` is current. If the repo has `tools/workspace_check.py`, run `python tools/workspace_check.py` before anything else; on `RESULT: workspace FAIL`, stop and tell the user to run `tools/setup-dev.ps1` in this folder (the project's setup skill explains each code). Do not work in an unconfigured folder.

CAMPAIGN START (when the user says "start <campaign>" from the main folder): leave the main folder where it is (on `main`). Clone a new folder from GitHub (`git clone <origin url> C:\Standalone\<repo>-<campaign>`), run that repo's setup script there (`tools/setup-dev.ps1`), create the branch `lane/<campaign>-<topic>` in it, and tell the user which folder to open the campaign session in. The main folder stays on `main`.

CONTEXT TO READ AT START:
- Last commit (`git log -1`, `git show HEAD`) for what shipped most recently
- Most recent devlog in `docs/devlogs/` — check frontmatter `approval` field for `approved` vs `pending`. This drives PHASE TRANSITIONS below.
- `docs/state.md` if it exists — slim snapshot of current focus, blockers, decisions pending. Read this for orientation.
- `AGENTS.md` Current Status section — high-level phase context. (CLAUDE.md is normally an `@AGENTS.md` import stub with no content of its own; read it only in legacy projects where it still carries full sections.)
- The current phase doc from `docs/phases/` (referenced in state.md or implementation-plan.md).

BEADS MIRROR (silent; doctrine `/beads-mirror`): only if the active phase doc's frontmatter has `beads_epic`, the project has `.beads/`, and `bd ready` exits 0. Pull (`bd dolt pull` when a remote is configured), then **Reconcile** the epic's children against git and the phase doc. After the planning audit passes, **Claim** the next row's bead: `bd dolt pull`, then `bd update <id> --claim --actor "<session-id>"`, then `bd dolt push`, back to back. Every bd write passes that `--actor`. A claim that is refused or contested (see `/beads-mirror` Claim) means another session holds the row: take the next row the phase doc allows in parallel, or stop. Never mention beads, bead IDs or claims in any reply to the user, including the final summary; record them only in the devlog's `beads:` line.

STATUS TABLE (doctrine: WORKFLOW.md, Status table): only if the project keeps a status table: `origin/main` carries a file whose frontmatter says `type: status-table` (`git grep -l '^type: status-table' origin/main -- docs`), and its `writer:` field names the tool that writes it. Read this campaign's row (`python <writer> show <campaign>`) and say in one line what it states. If the row is missing, or its tip is not the lane branch's pushed tip, say so; the first `/wrap` corrects it. When this session starts a campaign, set the row `running` with machine, lane branch and tip right after the branch's first push. Never edit the table in the lane folder: the writer commits the row on `main` without a checkout, so a landing never conflicts on it.

If the active instruction file's Current Status references a date older than ~2 weeks, surface it: "Current Status hasn't been updated in N days, may be stale." Don't auto-fix; let the user decide.

PLANNING AUDIT: Before starting any work, audit the next task for plan completeness. The next task should have a clear, written plan you can point to — a sub-phase entry in the implementation plan, a phase doc with pass criteria, or a saved plan file in the active agent plan directory (e.g. `~/.agents/plans/*.md`, `~/.codex/plans/*.md`, or `~/.claude/plans/*.md`). For each piece of upcoming work, verify:
- The scope is bounded (you know what is in and what is out)
- Pass criteria or definition-of-done is stated
- Dependencies and decisions are resolved (no open D-numbered questions blocking the work)
- Sub-phase decomposition exists if the work spans more than a single sitting
- If the phase will run under a goal, the phase doc has a Delegation section naming which sub-slices a worker may take, their allowed files and test commands (doctrine: `/delegate`)

If anything is unplanned, vague, or has unresolved decisions, STOP and enter plan mode first. Draft a plan, surface the open questions, and align before coding. For multi-week or multi-sub-phase work, suggest the user run `/plan-audit` (five parallel scouts: spec-alignment / acceptance-bar / toolchain-feasibility / decomposition / in-repo truth). The pattern caught 15 plan-level issues on Spike 5 before any code was written. Only proceed to implementation once the plan is concrete.

IMPORTANT: Do NOT ask for confirmation before proceeding once the plan is clear. After the planning audit passes (or after we've aligned on a fresh plan), immediately start working on the next task without waiting for my approval.

TESTING: Always test what you build before considering it done. This means actually running or opening the app to verify it works - not just getting it to compile. If it's a UI change, open the app and check it visually. If it's a feature, exercise the feature end-to-end. Don't wait for me to ask "did you actually try it?" - proactively verify your work functions correctly.

TOOLING: If you're having trouble testing something programmatically, don't just rely on manual verification - create better automation tooling. Expose what you need through the IPC/AutomationBridge so you can test it properly. The StateTree should give you access to verify state, and actions should let you drive the app. If something isn't exposed yet, add it.

PACING: Work continuously through subtasks without stopping. When you complete a subphase (4a, 4b, 4b.5, etc.), stop for review. If a phase has no subphases, complete the whole phase before stopping. This is where the session ends and I'll run /end-session to approve it.

PHASE TRANSITIONS: Read the most recent devlog's frontmatter `approval` field:
- `approval: approved` → previous sub-phase / phase is signed off. Start the next one immediately. Don't ask for approval again.
- `approval: pending` → work was in progress when the last session ended. Resume where it left off; don't treat it as a fresh start.

Only stop for approval when YOU just finished a sub-phase / phase in THIS session. Approval happens during `/end-session`, not `/start-session`.

If the project predates the frontmatter contract and devlogs use the old text marker instead of frontmatter, fall back to grepping for the literal regex `\*\*Phase\s+\S+\s*/\s*Subphase\s+\S+:\s*APPROVED\*\*` (matches `**Phase 4b / Subphase 4b: APPROVED**` etc.). If the legacy marker is found in the most recent devlog body, treat it as `approval: approved`. Suggest the user adopt the frontmatter contract going forward (e.g., by running `/slim-agent-md` and applying the new format on the next devlog).
