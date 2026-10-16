---
type: audit
summary: "Jev (TypeSafe System One) audit of the Agent Workflow Bundle: where skill prose asks the host agent for a fuzzy judgment that a calibrated typed answer would do better."
note_created: 2026-09-21
updated: 2026-09-21
---

# Jev audit — Agent Workflow Bundle

## Verdict

**8 real sites, all in skill prose; 0 in code.** The deterministic sweep found nothing because the bundle has no application code, only `SKILL.md` files plus two installers that do exact path work. Every judgment here is made by whichever host agent (Codex or Claude Code) happens to read the prose, against a rubric written in English. That is the Jev-shaped smell in this repo: the same rubric produces different verdicts on different days and different agents, and the skills then **act autonomously** on those verdicts (edit a plan, apply a fix, move a section, commit).

**Best first move:** a proof-altitude screen for pass criteria (Site 1). It is the bundle's flagship doctrine, it is enforced today only by an Explore agent reading a paragraph, and the live probe below already reproduces the doctrine's own verdicts on the example phase doc with calibrated probabilities.

One constraint shapes every recommendation: the bundle is a **portable, dependency-free** folder. Any Jev integration must be optional, a small helper script invoked only when `TYPESAFE_API_KEY` is set, with the current prose rubric as the fallback. Jev judges; the skill prose still owns the workflow, thresholds, and side effects.

## How the sweep was done

1. `scan.py` over the repo: no candidate files (it scans code extensions only; the repo is `.md`, `.ps1`, `.sh`).
2. Read every `SKILL.md`, both installers, the example skeleton, and the top-level docs.
3. For each skill, asked: what does it show, select, change, or hand off, and how is that decision made today?

## Ranked sites (best win per effort first)

### 1. Proof-altitude screen for pass criteria

| | |
|---|---|
| where | `skills/plan-audit/SKILL.md:47` (acceptance-bar agent), `skills/formalize-plan/SKILL.md:15` ("the criterion must bite"), `skills/slash-goal/SKILL.md:74` (rule 6), `skills/start-session/SKILL.md:19` (planning audit) |
| judgment | Could a stubbed or placeholder build clear this pass criterion? And at what altitude does it prove the feature: artifact-exists, readback, behavioral, visible-asserted? |
| today | An Explore agent is handed a 300-word rubric and asked to flag criteria. Four skills restate the same rubric in slightly different words. No probability, no consistent bar across Codex vs Claude, and the check is skipped entirely for "routine" phases. |
| primitive | Noul (`mock_can_pass`) plus Score (`altitude`, 4 levels), one pair per criterion, batched in one request |
| state | `{"criteria": {"<id>": "<criterion text>"}, "phase_context": "<Overview paragraph>", "user_facing": true/false}` |
| policy | `mock_can_pass >= 0.75` or `altitude < 2` on a user-facing phase → the plan-audit agent must rewrite the criterion (derived fix). Score confidence `< 0.3` → hand the criterion to the agent for a full read, don't auto-flag. |
| win | correctness + consistency across agents; removes four divergent copies of the rubric |
| effort | M: a `scripts/jev/proof-altitude.py` that takes a phase doc path, extracts `Verification:` / `Success Criteria` lines, returns JSON. Skills call it when the key is set. |
| cookbook | guardrails / citation check (verify a claim against its evidence, escalate the uncertain) |

Ready-to-paste question (one pair per criterion id `k`):

```json
{
  "mock_k": {
    "type": "noul",
    "instructions": "Could a stubbed, placeholder, or model-only build pass pass criterion `criteria.k` without the real feature existing?",
    "criteria": {
      "true": "Only a proxy layer is checked: a readback returns expected JSON, a log line appears, a file or capture exists, a tool call returns without error. Canned data would clear it.",
      "false": "False unless the real experience exists: a human sees specific content, an action produces an observable change, execution output changes, or an assertion on capture content (vision_eval style) is required."
    }
  },
  "alt_k": {
    "type": "score",
    "instructions": "Rate the proof altitude of pass criterion `criteria.k`.",
    "criteria": [
      "artifact-exists: only checks that something was produced or a call returned",
      "readback: returned values match expectation, no visible or behavioral gate",
      "behavioral: the feature must execute and its output must change observably",
      "visible-asserted: a human-visible result with an assertion on what must be seen"
    ]
  }
}
```

### 2. Auto-apply guardrail for audit findings

| | |
|---|---|
| where | `skills/audit/SKILL.md:48-56` (ship-blocking / must-fix / should-fix / larger / defer; "apply now criterion"), `skills/plan-audit/SKILL.md:67-75` (derived / judgement-call / unresolvable) |
| judgment | Is this finding safe to apply without the user: small, mechanical, no new architecture, no design choice the user hasn't made? And which bucket is it? |
| today | The synthesizing agent sorts free-text findings by feel. Both skills then **edit files autonomously** on that sort. A mis-bucketed "judgement call" becomes a silent design decision. |
| primitive | Choice over the bucket set (with `unclear`) plus Noul `safe_to_auto_apply`, per finding, batched |
| state | `{"finding": {"agent": ..., "claim": ..., "proposed_change": ..., "citation": ...}, "doctrine": "<apply-now criterion text>"}` |
| policy | apply only when `safe_to_auto_apply >= 0.8` and Choice confidence `>= 0.6`; anything else goes to the "judgement calls to review" list the skill already prints. Never lowers the bar: a high probability still needs the citation verified, as the skill says. |
| win | robustness: the autonomous edit gets a calibrated gate instead of a vibe |
| effort | M (findings must be assembled as named fields before the call; the agents already report in a fixed shape) |
| cookbook | SDE cascade (cheap judge first, escalate uncertain cases to the reasoning agent or human) |

```json
{
  "bucket": {
    "type": "choice",
    "instructions": "Sort audit finding `finding` per `doctrine` into the bucket the skill should use.",
    "criteria": {
      "derived_fix": "Mechanical and unambiguous: missing pass criterion, unnamed dependency, dangling citation, wrong version corrected with evidence",
      "judgement_call": "Resolving it requires a choice on the user's behalf: dropping a deliverable, picking a replacement library, adding a sub-phase, restructuring",
      "unresolvable": "No defensible best guess exists from spec, research, conversation, or codebase",
      "not_a_finding": "The agent reviewed it and it is fine as is",
      "unclear": "The finding text does not carry enough to decide"
    }
  },
  "safe_to_auto_apply": {
    "type": "noul",
    "instructions": "Is applying `finding.proposed_change` without asking the user consistent with `doctrine`?",
    "criteria": {
      "true": "Small, mechanical, adds no architecture, requires no design decision the user has not made",
      "false": "Expands scope, picks between designs, touches something irreversible, or rests on an unverified claim"
    }
  }
}
```

### 3. Section verdict in `/slim-claude-md`

| | |
|---|---|
| where | `skills/slim-claude-md/SKILL.md:105-118` (Keep / Compress / Extract to knowledge / Extract to skill / Merge / Delete), plus the three shape tests at lines 42-81 (knowledge-shaped, lessons-shaped, skill-shaped) |
| judgment | Which of six destinations does this `##` section belong in? |
| today | The agent walks headings with a table of prose definitions. "Delete" is guarded by "verify against code", good, but the other five are judged inconsistently, and a 30K-char file has 20+ sections to sort in one pass. |
| primitive | Choice with the six verdicts plus `unclear`, one per section, batched in one request |
| state | `{"sections": {"<slug>": "<heading + first ~600 chars>"}, "policy": "<what stays / what moves table>"}` |
| policy | confidence `>= 0.7` → pre-fill the Step 3 plan; below → list the section as an open question in the plan (the skill already has that slot, line 155). `delete` never auto-applies regardless of probability. |
| win | consistency, and the plan table gets a confidence column the user can scan |
| effort | S: the skill already emits a per-section table; the call slots in before Step 3 |
| cookbook | hierarchical classification / intent routing |

Probe 2 below ran this exact question on four sections of this repo's own `AGENTS.md`.

### 4. Cross-project applicability in `/extract-playbook`

| | |
|---|---|
| where | `skills/extract-playbook/SKILL.md:58-63` (High / Medium / Low), rule 1 line 147 (the "cross-project test"), Step 5 line 116 ("phrasing that's still project-specific") |
| judgment | Would this pattern recur in a new project with a similar stack? And does the draft still leak project-specific names? |
| today | Three-level rubric applied by feel; the leak check is a re-read. |
| primitive | Score (3 levels: project-specific / library-specific / stack-agnostic) per candidate section; Noul `leaks_project_names` per draft paragraph |
| state | `{"section": "...", "project": {"name": ..., "custom_terms": [...]}}` |
| policy | surface candidates with score `>= 1.5` first; paragraphs with `leaks >= 0.6` get highlighted in the Step 5 review |
| win | new capability (the leak check) + consistency |
| effort | S |
| cookbook | composite scoring |

### 5. Rerank in `/lookup`

| | |
|---|---|
| where | `skills/lookup/SKILL.md:38-45` (`grep -rl "<keyword>"`), line 66 ("frontmatter exact match > body match") |
| judgment | Which of these knowledge files and playbooks actually answer the question? |
| today | Literal grep on 1-3 keywords, then a hand-ranking rule. Rule 3 (line 72) even forbids substituting "ZeroMQ" for "ZMQ", so a paraphrase misses. A body mention in an unrelated file outranks a relevant file whose keywords use a synonym. |
| primitive | Score `relevance` (4 levels) per candidate, batched over the INDEX rows plus grep hits |
| state | `{"query": "...", "candidates": {"<file>": {"keywords": [...], "summary": "...", "matched_line": "..."}}}` |
| policy | code still does the grep and reads the INDEX table (that is the candidate set); Jev orders it and drops `< 1`. Keep rule 3's honesty: report both spellings when both appear. |
| win | robustness to paraphrase; cheaper than reading every hit |
| effort | S |
| cookbook | reranking |

### 6. Lesson qualifier in `/end-session` Phase 5

| | |
|---|---|
| where | `skills/end-session/SKILL.md:79-89` |
| judgment | Is this issue a gotcha worth a `lessons.md` entry, or trivia? |
| today | Four prose signals; "don't pad lessons.md with trivia" is the only brake. |
| primitive | Noul `worth_a_lesson` per "Issues Encountered" bullet |
| state | `{"issue": "...", "attempts": N, "resolved_by": "..."}` |
| policy | `>= 0.7` write; `0.4-0.7` write with `Frequency: one-time`; below skip |
| win | consistency; keeps lessons.md from silting |
| effort | S |
| cookbook | guardrails |

### 7. Style guard in `/audit` spec agent

| | |
|---|---|
| where | `skills/audit/SKILL.md:40` ("contrastive phrasing", "conversation leaks"), line 62 (detect the rule by grepping for "no em dashes" or "em-dash") |
| judgment | Does this changed paragraph violate the project's writing rules? And does the instruction file actually forbid em dashes? |
| today | The em-dash rule is detected by **keyword grep on the instruction file**, the one literal surface-form classifier in the bundle. "Contrastive phrasing" and "conversation leak" are undefined at runtime. |
| primitive | Noul `forbids_em_dashes` over the instruction file's style section (once); Noul `conversation_leak` and `contrastive_phrasing` per changed paragraph |
| policy | flag only; the skill already restricts fixes to session-modified files |
| win | correctness of the rule detection; removes a grep that fails on "avoid the em dash" |
| effort | S |
| cookbook | guardrails |

### 8. Phase-boundary check in `/wrap`

| | |
|---|---|
| where | `skills/wrap/SKILL.md:53-57` ("the slice you just closed completes the whole phase → run /end-session") |
| judgment | Did this slice finish the phase, or just a sub-slice? |
| today | Agent's own sense of the plan; a wrong call either skips the approval ceremony or triggers it early. |
| primitive | Noul `phase_complete` over `{"phase_doc_subphases": [...], "devlogs_closed": [...], "this_slice": ...}` |
| policy | `>= 0.8` stop and suggest `/end-session`; else roll on. Never auto-runs `/end-session`. |
| win | robustness in overnight `slash goal` runs, where a wrong roll-through is the expensive failure |
| effort | S |
| cookbook | guardrails |

## Not worth it

Sites considered and rejected; these stay as exact code or prose rules.

- **`scripts/install.ps1` conflict detection** (lines 110-135). Exact path existence. Lookup, not judgment.
- **`/start-session` legacy APPROVED marker** (line 41). The regex parses a fixed format. Not a judgment.
- **`/find-session` "interrupted" detection** (line 47). Literal `[Request interrupted by user]` string. Exact.
- **Size thresholds** (25K / 40K chars in `/slim`, `/end-session` Phase 7) and **staleness** (90 days in `/audit-playbooks`, 2 weeks in `/start-session`). Arithmetic on a policy number.
- **Frontmatter schema audit** (`/end-session` Phase 6). YAML parse plus required-field presence. Exact.
- **INDEX consistency** (`/audit-playbooks` Step 3). Set difference between files and rows.
- **Session-relevant file list** (`/end-session` Phase 10). Sourced from the agent's own tool-call history. Exact, and correctly so.
- **Devlog path choice** (`/end-session` Phase 1: code vs no-code session). `git diff` non-empty is a fine rule.
- **`/find-session` "what was the session about"**. That is summarization, not a typed judgment; leave it to the host agent.
- **`/audit-playbooks` Deep mode claim verification.** A citation-check Noul fits ("does this doc excerpt contradict this claim?"), but the expensive part is fetching the right doc page, which Jev cannot do. Revisit only if Deep mode gets used.
- **`/plan-audit` MEASURED vs ASSUMED labelling** (line 57). Provenance tracing through the repo; the judgment is trivial once the receipt is found, and finding it is the work.

## Probe results

Two live requests, `jev-latest`, run 2026-09-21. Cost is fractions of a cent.

**Probe 1: Site 1 on the five real criteria in `example-skeleton/docs/phases/phase-1-mcp-foundation.md`.** Input tokens: 1716.

| criterion | text (abridged) | mock can pass | altitude (0-3) | score conf |
|---|---|---|---|---|
| 1a | invoke the MCP tool, see `pong` | 0.65 | 2.60 | 0.60 |
| 1b | set a parameter, read back the new value | **0.86** | 1.04 | 0.96 |
| 1c | captures the window, sees rendered output as an image | 0.76 | 2.04 | 0.04 |
| sc2 | PING round-trip latency under 5ms | **0.82** | 1.19 | 0.75 |
| sc4 | screenshot capture works on the target OS | 0.78 | 1.21 | 0.00 |

Read against the bundle's own doctrine: 1b is a pure readback and Jev says so with high confidence. 1c is exactly the "screenshot captured, no assertion on content" case that `formalize-plan` line 15 calls insufficient, and Jev flags it mock-passable at 0.76 while spreading the altitude score (conf 0.04), which is the right signal to hand it to the agent for a rewrite rather than auto-flag. sc4 gets confidence 0.00 on altitude: the criterion says nothing about proof at all, and the distribution shows it. What the current prose produces here today depends on which agent reads it; there is no number to compare.

**Probe 2: Site 3 on four sections of this repo's `AGENTS.md`.** Input tokens: 1411.

| section | verdict | conf | runner-up |
|---|---|---|---|
| Visual graph | delete | 0.22 | extract_to_knowledge 0.30 |
| Deploy discipline | keep | 0.26 | extract_to_knowledge 0.37 |
| Conventions & doctrine | keep | 0.94 | compress 0.04 |
| Commit & git | keep | 0.81 | compress 0.13 |

The two confident verdicts are the two a maintainer would make. The two split verdicts are the two genuinely arguable sections (the graph duplicates `WORKFLOW.md`; deploy discipline is reference-shaped but read every session), and the policy in Site 3 routes exactly those to the human. That is the behavior the bundle wants from a slim plan.

## Next step

**Site 1 is built (2026-09-21):** `skills/plan-audit/scripts/proof-altitude.py`, wired into `/plan-audit` Step 2b. It lives inside the skill folder, not the top-level `scripts/`, because the installer copies only `skills/`. The prompt below is kept as the record of what was asked for; Site 2 is the next candidate.

Original prompt for `/typesafe:typesafe-ai`:

> In `C:\Standalone\agent-workflow-bundle`, add an optional helper `scripts/jev/proof-altitude.py` (stdlib only, no SDK) that takes a phase doc path, extracts each `**Verification**:` line and each `## Success Criteria` bullet, and POSTs one batched request to `https://api.typesafe.ai/v1/systemone` with the `mock_k` Noul and `alt_k` Score pair from `docs/jev-audit.md` Site 1, using `TYPESAFE_API_KEY` from the environment. Print a table: criterion id, text, mock_can_pass, altitude, confidence, and a verdict column using the policy `mock >= 0.75 or altitude < 2 → REWRITE`, `score confidence < 0.3 → READ`. Exit 0 always. Then edit `skills/plan-audit/SKILL.md` Step 3 so the acceptance-bar agent runs the script when the key is set and treats its REWRITE rows as derived fixes and READ rows as findings to examine, falling back to the current prose rubric when the key is absent. Keep the skill's existing agent prompt; do not add the key to any file. Update README.md and INSTALL.md with a one-line note that the helper is optional.
