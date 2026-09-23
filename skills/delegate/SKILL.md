---
name: delegate
description: The bundle's model-tiering doctrine. Cheap-tier scouts read and report, cheap-tier workers implement one sub-slice each, the session is the only judge whatever frontier model it happens to run, and Jev screens every handoff. Other skills cite this; invoke it directly to see the branching map, the check protocol, or how to name a role on each runner.
allowed-tools: Read, Glob, Grep, Bash(python:*), Bash(git diff:*), Bash(git status:*)
user-invocable: true
---

# Delegate

One sentence other skills use: **Delegation follows `/delegate`: scouts read, workers implement inside their slice, the session judges, Jev screens.**

## Roles

| Role | May | May never | Claude Code | Codex |
|---|---|---|---|---|
| **scout** | read, search, run read-only commands, fetch docs, report with `file:line` | edit, write, commit, decide | agent `scout`, `model: sonnet`, no shell | agent `scout`, `gpt-6-luna` low |
| **worker** | edit files inside its assigned sub-slice, run that slice's tests, draft a doc, report files + test output + evidence | touch files outside the slice, edit plans or instruction files, commit, push, approve | agent `worker`, `model: sonnet`, bare Bash (git ban is prose + protocol) | agent `worker`, `gpt-6-luna` medium |
| **judge** | orient, author, synthesize, verify, apply, approve, commit | delegate a judgment | the session | the session |
| **screen** | return calibrated typed answers at handoffs | execute anything | Jev via `TYPESAFE_API_KEY`, optional | same |

The judge is never a subagent. Workers never commit. If a skill needs a judgment, it runs it in the session.

Safety net: `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` (Claude settings `env`) and `[agents] default_subagent_model = "gpt-6-luna"` (Codex config) catch any spawn that forgot to name a role. The installer prints these; add them by hand.

## How to name a role

- **Claude Code**: call the `Agent` tool with `subagent_type: "scout"` or `subagent_type: "worker"`. Start the prompt with `ROLE:scout` or `ROLE:worker` so `/tier-check` can identify the transcript.
- **Codex**: write "spawn the `scout` agent" or "spawn the `worker` agent" in the instruction, and start the spawn prompt with `ROLE:scout` / `ROLE:worker`.
- Both: the prompt is self-contained (the agent has not seen the conversation), names the exact files, and for a worker names the pass criterion, the allowed files, and the test command.
- If the runner reports that `scout` or `worker` is not a known agent type, the definitions are not installed or the agent was not restarted after install. For ordinary work, fall back to `general-purpose` with `model: sonnet` (Codex: rely on `[agents] default_subagent_model`), keep the `ROLE:` marker, and say in the report that the fallback was used. Never use the fallback for a `/tier-check` proof run.

## The branching map

```
                 JUDGE (session)                   CHEAP TIER                                SCREEN (Jev)
/start-session   orient, planning audit            -                                         -
/formalize-plan  author the contract               -                                         -
/spec-draft
/research-prompt

/plan-audit      read ctx ---------------------->  5 scouts, one per lens, report -------->  proof-altitude
                 fix plan <-- ranked findings <----------------------------------------- finding-triage
/audit           scope diff -------------------->  3 scouts report ---------------------->  finding-triage
                 apply safe / surface rest <------------------------------------------------

slash-goal loop  per sub-slice the phase doc marks delegable:
                 dispatch slice ---------------->  worker implements + runs tests
                 CHECK (below)              <----  files, test output, evidence
                                                                                        diff-risk
                 accept -> /wrap  |  reject -> re-dispatch (max 2) -> then do it itself
/wrap /checkpoint /end-session   judge only

/lookup /find-session            scout collects -> judge summarizes (not yet routed)
/audit-playbooks deep            scouts verify claims -> judge decides
/extract-playbook /slim          worker drafts the file -> judge reviews, applies (not yet routed)
```

Rows that stay on the judge stay there because orientation and plan authoring are the judgment itself, and the closers need the session's own memory and own every git operation.

## The check protocol

A worker's report is a claim, not evidence. Before anything a worker did reaches `/wrap`:

1. **Scope.** Record HEAD before dispatch. After the worker returns, `git rev-parse HEAD` must equal it; a worker that committed fails here. Run `git diff --stat` and compare with the files the worker says it touched and the slice's allowed files. Any file outside the slice: reject without reading further.
2. **Tests.** Run the slice's test command yourself. The worker's pasted output does not count.
3. **Screen.** Build `{"slice": {...}, "hunks": [{"id","file","summary"}]}` from the diff (one hunk per file or per logical change, a one-line summary each) and pipe it to `python <delegate skill base dir>/scripts/jev-screen.py diff-risk`. It returns `needs_close_review` per hunk and a `slice_status`. If it prints `skipped:`, read in file order instead.
4. **Read.** Every hunk, in descending `needs_close_review`. The screen orders; it never excuses a hunk.
5. **Decide.** `meets_criterion` and you agree after reading: proceed to `/wrap`. Otherwise re-dispatch the worker with your findings as the prompt (same role, same slice, same limits). After **max 2** rejections, finish the slice yourself and append a lesson to `docs/lessons.md` saying what the worker got wrong, so the next phase doc can mark that kind of slice non-delegable.

Scout reports get the lighter version. Collect each finding as `{"id","agent","claim","proposed_change","citation"}`, put the skill's apply-now criterion in `doctrine`, pipe to `python <delegate skill base dir>/scripts/jev-screen.py finding-triage`, and read findings in verdict order: `ASK` first (open questions for the user), then `REVIEW`, then `AUTO_APPLY`. Verify the citation of every `AUTO_APPLY` before applying; never auto-apply a finding whose `safe_to_auto_apply` is below 0.8, whatever its bucket. If the screen is skipped, apply the skill's own triage rubric unchanged.

## What the phase doc must carry

`/formalize-plan` writes a **Delegation** section next to **Autonomy & human-in-the-loop**: which sub-slices a worker may take and which the judge keeps, the allowed files per delegable slice, the test command per delegable slice, and the retry budget (default 2). A delegable slice without a file list or a test command is a plan defect; `/plan-audit`'s decomposition agent flags it. `/slash-goal` points at the section rather than restating it.

## Rules

1. **Cheap tier reads and implements; the session judges.** No exceptions for "small" judgments.
2. **Workers never commit, never touch plans or instruction files, never leave their slice.**
3. **Every worker diff goes through the check protocol.** Scope, tests you ran, screen, read all, decide.
4. **Jev orders and gates; it never excuses reading or applies anything.** Skipped screen means the prose rubric, not a free pass.
5. **Mark every dispatched prompt with `ROLE:<name>`** so `/tier-check` can prove the tier from transcripts.
6. **Two rejections, then the judge does it.** Log the lesson.
7. **The judge is a tier, not a named model.** Whatever frontier model the session runs is the judge — it changes between sessions and sometimes mid-session. Never pin a model name in a skill, a goal, or a report, and pass `/tier-check` the `--main` prefix you are actually on.

## What NOT to do

- Don't spawn Explore or a generic agent for reading when a scout exists; the generic one inherits the frontier model.
- Don't hand a worker a slice whose pass criterion it cannot run itself.
- Don't let a passing test output in a worker's report stand in for running it.
- Don't skip the read because the screen said low risk.
