---
type: design
status: approved
summary: "Model tiering for the bundle: cheap scout/worker agents do the menial work on both runners, the frontier session judges, Jev screens every handoff, and a transcript-based tier-check proves which model ran."
note_created: 2026-09-22
updated: 2026-09-22
---

# Model tiering: scouts, workers, a judge, and a screen

## Problem

Every skill in the bundle that spawns agents (`/audit`, `/plan-audit`, deep `/audit-playbooks`) spawns them on the session's own model, because on Claude Code the built-in Explore agent inherits the session model and on Codex spawned threads inherit the parent's model unless told otherwise. A frontier session therefore runs five frontier reporters to read a phase doc, and a frontier campaign implements every sub-slice on that same expensive model. The frontier model is spent on reading and drafting, the cheap tier is unused, and nothing records which model actually did what.

The user runs the workflow skills in Claude Code and the slash-goal campaigns in Codex, each on whatever frontier model that runner is set to at the time. Both runners must delegate the same way, from the same prose, and the delegation must be provable. The judge is a tier, not a named model: it changes under you, sometimes mid-session.

## Verified facts this design rests on (2026-09-22)

| Runner | Fact | Source |
|---|---|---|
| Claude Code | Agent definition frontmatter `model:` accepts `sonnet`, `opus`, `haiku`, `fable`, full IDs, `inherit`; default is the session model | code.claude.com/docs/en/sub-agents.md, frontmatter reference |
| Claude Code | Agent tool takes a per-call `model`; resolution: per-call, then definition, then `CLAUDE_CODE_SUBAGENT_MODEL` env, then session | same, model resolution order |
| Claude Code | `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` overrides everything; Explore inherits the session model | same, built-in subagents |
| Claude Code | Each subagent's transcript is `<projects>/<key>/<session>/subagents/agent-<id>.jsonl`, every assistant line carries `"model":"<id>"` | inspected this session: the claude-code-guide agent's file shows `claude-haiku-4-5-20251001` on 18 lines |
| Codex | Custom agents are TOML files in `~/.codex/agents/` or `.codex/agents/`; required `name`, `description`, `developer_instructions`; optional `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config` | learn.chatgpt.com/docs/agent-configuration/subagents |
| Codex | `config.toml` `[agents]` has `default_subagent_model`, `default_subagent_reasoning_effort`, `max_concurrent_threads_per_session`; precedence explicit spawn, then `[agents]`, then parent | same |
| Codex | Skill instructions and AGENTS.md may request delegation; a spawn prompt may name the model | same |
| Codex | Rollout JSONL under `~/.codex/sessions/YYYY/MM/DD/` carries `thread_settings_applied` events with `thread_settings.model`, `reasoning_effort`, `thread_id` | inspected this session |
| Codex | Models available on this machine include `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-*`, `gpt-5.5` | `~/.codex/models_cache.json` |

Things NOT verified and therefore not relied on: whether a Codex spawn tool exposes `model` as a structured field (an unofficial `multi_agent_v2` flag exists; this design uses agent files and the `[agents]` defaults, which are documented, and never the flag).

## Roles

| Role | What it may do | What it may never do | Claude Code | Codex |
|---|---|---|---|---|
| **scout** | read files, run read-only commands, search, fetch docs, report | edit, write, commit, decide | `~/.claude/agents/scout.md`, `model: sonnet` | `~/.codex/agents/scout.toml`, `model = "gpt-6-luna"`, `model_reasoning_effort = "low"` |
| **worker** | edit files inside its assigned sub-slice, run the slice's tests, draft a doc, report files touched + test output + evidence | touch files outside the slice, edit plans or instruction files, commit, push, approve | `~/.claude/agents/worker.md`, `model: sonnet` | `~/.codex/agents/worker.toml`, `model = "gpt-6-luna"`, `model_reasoning_effort = "medium"` |
| **judge** | everything else: orient, author plans, synthesize, verify, apply fixes, approve, commit | delegate a judgment | the session itself, on whatever frontier model it runs | the session itself, on whatever frontier model it runs |
| **screen** | return calibrated typed answers at handoffs | execute anything | Jev via `TYPESAFE_API_KEY`, optional | same |

The judge is never a subagent. A skill that needs judgment runs it in the session.

Safety net: `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` in the Claude settings env and `[agents] default_subagent_model = "gpt-6-luna"` in Codex config, so an agent spawned without a role still lands on the cheap tier. The installer prints these snippets and never writes them (INSTALL.md promises it does not touch `settings.json`; the same promise extends to `config.toml`).

## The branching map

```
                 JUDGE (the session)               CHEAP TIER (sonnet / gpt-6-luna)         SCREEN (Jev)
/start-session   orient, planning audit            -                                        -
/formalize-plan  author the contract               -                                        -
/spec-draft
/research-prompt

/plan-audit      read ctx ---------------------->  5 scouts, one per lens, report ------->  proof-altitude (built)
                 fix plan <-- ranked findings <---------------------------------------- finding-triage
/audit           scope diff -------------------->  3 scouts report --------------------->  finding-triage
                 apply safe / surface rest <-----------------------------------------------

slash-goal loop  per sub-slice marked delegable in the phase doc:
                 dispatch slice ---------------->  worker implements + runs tests
                 CHECK (below)              <----  files, test output, evidence
                                                                                       diff-risk
                 accept -> /wrap  |  reject -> re-dispatch (max 2) -> then do it itself
/wrap /checkpoint /end-session   judge only

/lookup /find-session            scout collects -> judge summarizes (not yet routed)
/audit-playbooks deep            scouts verify claims -> judge decides
/extract-playbook /slim          worker drafts the file -> judge reviews, applies (not yet routed)
```

Rows that stay on the judge stay there for a reason: orientation and plan authoring are the judgment itself; the three closers need the session's own memory of what happened and own every git operation.

## The check protocol

A worker's report is a claim. Before anything a worker did can reach `/wrap`, the judge:

1. **Scope.** `git diff --stat` against the worker's claimed file list. Any file outside the sub-slice's declared files: reject, no further reading.
2. **Tests.** Re-run the slice's test command itself. The worker's pasted output is not evidence.
3. **Screen.** Run `jev-screen.py diff-risk` over the hunks (one Noul `needs_close_review` per hunk summary, one Choice `slice_status` over the whole diff: `meets_criterion`, `partial`, `off_scope`, `unclear`). Skipped cleanly when the key is absent.
4. **Read.** Hunks in descending `needs_close_review`; every hunk, not only the flagged ones. The screen orders, it does not excuse.
5. **Decide.** `meets_criterion` and the judge agrees: `/wrap`. Otherwise re-dispatch the worker with the findings as its prompt. After two rejections the judge finishes the slice itself and appends a lesson to `docs/lessons.md` naming what the worker got wrong, so the next phase doc can mark that kind of slice non-delegable.

Scout reports get the lighter version: `jev-screen.py finding-triage` (the Site 2 questions from `docs/jev-audit.md`: bucket Choice plus `safe_to_auto_apply` Noul) runs before synthesis; the judge reads findings in risk order and never auto-applies one with `safe_to_auto_apply < 0.8`, whatever the bucket says.

## What the phase doc must say

`/formalize-plan` adds a **Delegation** section beside **Autonomy & human-in-the-loop**:

- which sub-slices a worker may take (default: any slice whose pass criterion is a test or an executing check the worker can run itself), which the judge keeps (anything touching the spec, instruction files, git, or an unsettled decision), and the files each delegable slice is allowed to touch;
- the test command per delegable slice;
- retry budget (default 2).

`/slash-goal`'s default goal gains one clause: "delegate sub-slices per the phase doc's Delegation section and check each per the delegate doctrine." `/plan-audit`'s decomposition agent flags a delegable slice with no file list or no test command.

## Files

New:

| Path | Purpose |
|---|---|
| `agents/claude/scout.md`, `agents/claude/worker.md` | Claude Code agent definitions, `model: sonnet`, least-privilege tools (scout: read-only; worker: Read, Edit, Write, Glob, Grep, Bash without git) |
| `agents/codex/scout.toml`, `agents/codex/worker.toml` | Codex agent definitions, `gpt-6-luna`, matching `developer_instructions` |
| `skills/delegate/SKILL.md` | The doctrine above: roles, branching map, check protocol, how a skill names a role on each runner. Other skills cite it in one sentence. |
| `skills/delegate/scripts/jev-screen.py` | Two question sets (`finding-triage`, `diff-risk`), stdin JSON in, JSON out, same `skipped:` contract as `proof-altitude.py`, stdlib only |
| `skills/delegate/scripts/tier-check.py` | Reads the runner's transcripts since a start timestamp and asserts each named agent ran on the expected model; `--expect` overridable so the check can be made to fail |
| `skills/tier-check/SKILL.md` | User-invocable: spawns scout and worker on a trivial task, then runs `tier-check.py` and reports PASS/FAIL per agent with the model ID seen |

Changed:

| Path | Change |
|---|---|
| `scripts/install.ps1`, `scripts/install.sh` | Also copy `agents/claude/*` to `<root>/agents/` for the claude target and `agents/codex/*` for codex; same conflict rule; print the env / config snippets at the end |
| `skills/audit/SKILL.md`, `skills/plan-audit/SKILL.md` | Spawn `scout` (Claude: `subagent_type=scout`; Codex: "spawn the scout agent") instead of Explore; run finding-triage before synthesis |
| `skills/slash-goal/SKILL.md` | Default goal gains the delegation clause |
| `skills/formalize-plan/SKILL.md`, `skills/scaffold-project/templates/phase-template.md` | Delegation section |
| `skills/start-session/SKILL.md` | Planning audit checks the Delegation section exists when the phase will run under a goal |
| `skills/wrap/SKILL.md` | One line: a slice a worker implemented reaches `/wrap` only after the check protocol |
| `README.md`, `WORKFLOW.md`, `INSTALL.md`, `AGENTS.md` | Catalog rows, narrative, install of agents + snippets, repository structure |

## Proving it works

| Test | What it proves | Runner | Pass condition |
|---|---|---|---|
| T1 | Agents install | both | dry-run lists 2 files per target; after install, hashes of installed files equal bundle source |
| T2 | Claude delegation is real | Claude Code | `/tier-check` spawns scout + worker; `tier-check.py --runner claude` finds both new `subagents/agent-*.jsonl` files with every `model` matching `claude-sonnet-*` and the main transcript's last assistant `model` matching `claude-fable-*` |
| T3 | Codex delegation is real | Codex | `/tier-check` spawns scout + worker; `tier-check.py --runner codex` finds `thread_settings_applied` events with `model = gpt-6-luna` on thread ids other than the parent's, and the parent's on `gpt-6-astra` |
| T4 | The detector can fail | both | `tier-check.py --expect claude-opus-` (or `--expect gpt-6-sol`) on the same transcripts exits non-zero and names the mismatching model |
| T5 | The check protocol end to end | Claude Code first, then Codex | On `example-skeleton`, a doc-only sub-slice is dispatched to a worker; scope, tests, diff-risk, read, decide all run; `/wrap` produces one commit whose files equal the slice's declared list |
| T6 | Screens fail open | both | With `TYPESAFE_API_KEY` unset, `jev-screen.py` and `proof-altitude.py` print `skipped:` and the skills continue |

T2, T4, T6 and the Claude halves of T1 and T5 run from the current Claude Code session. T3 and the Codex halves must be run by the user in Codex; the scripts carry the assertions so the output has the same shape.

## Out of scope

- A coded orchestration pipeline (Workflow scripts, Codex batch). The doctrine stays prose so it ports.
- Two cheap rungs (haiku / gpt-5.5 for scans). Revisit if scouts prove too slow or too expensive on sonnet / luna.
- Jev rerank for `/lookup` (Site 5 of the audit). Independent, later.
- Any change to what the judge does; this design only moves reading and implementing off it.

## Decisions taken during design

- Cheap tier is one rung below frontier (sonnet / gpt-6-luna), not two. Chosen for implementation quality on sub-slices.
- Workers implement sub-slices, not only drafts. Chosen for savings; the check protocol is the price.
- The env fallback is kept alongside named roles, so an unnamed spawn is still cheap.
- Agent files ship in the bundle and are installed; the env snippets are printed, not written.
