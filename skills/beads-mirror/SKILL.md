---
name: beads-mirror
description: Doctrine for mirroring a formalized campaign into beads so parallel sessions can't take the same row and other people can see where the work stands. Beads is a derived mirror; commits and the campaign doc stay the truth. Fully automatic and invisible to the user. The session skills cite it; invoke it directly as `/beads-mirror adopt` (inside a campaign's session) or `/beads-mirror adopt <phase-doc>` to opt an already-formalized campaign in.
allowed-tools: Read, Edit, Glob, Grep, Bash(bd:*), Bash(git:*)
user-invocable: true
---

# Beads Mirror

Commits and the canonical campaign doc (phase doc / contract) are the ground truth. Beads is a **mirror** of them with two jobs:

1. **Claim safety**: a session claims the row it works on, so a parallel session can't start the same row.
2. **Visibility**: anyone can run `bd ready` / `bd list` and see where the campaign stands without reading the contract.

Beads never holds a pass criterion, a ruling or a decision. When beads disagrees with git or the campaign doc, beads is rewritten from them, never the other way round.

## Invisible by design

- **Never ask the user** anything about beads.
- **Never mention beads in any reply to the user**: no bead IDs, claims, closes, pushes, skipped steps or leftover beads. This applies to final summaries too. Beads appears only in the commit subject's `[<id>]` and in the devlog's `beads:` line. Never stop or slow a session because of beads.
- Every beads action in a session is recorded as **one line in that session's devlog**: `beads: <what changed>`, or `beads: skipped — <reason>`.
- A beads command that fails is logged in that line and the session carries on. The one exception, which changes what a session does, is a claim refused because another live session holds the row (see Claim below).

## Activation guard

Beads steps run only when **all three** hold. Otherwise do nothing and write nothing.

1. The active phase doc's frontmatter has `beads_epic: <id>`. This is the opt-in; a campaign without it is untouched, whatever else the project does.
2. The project has a `.beads/` directory.
3. `bd ready` exits 0. Use `bd ready` for health, never `bd prime`, which exits 0 even when the database can't be opened.

If (1) holds but (2) or (3) fails, log `beads: skipped — <reason>` in the devlog and carry on.

## Identity

Decide the session id once, at the first beads step, and write it into the devlog's `beads:` line. **Every** `bd` write in the session (create, claim, note, heartbeat, close, unclaim) passes `--actor "<session-id>"`; a write without it falls back to the shared git user name and defeats the claim. The session id is, where `<session-id>` is the project's commit Session-Id value if it has one (for example `alex/2026-09-23/save-wave-1`), otherwise `<git user.name>/<YYYY-MM-DD>/<session-slug>`. Use one value for the whole session. Without a per-session actor, two sessions run by the same person look like one claimant and both "win" the same claim.

## Row ↔ bead mapping

- One **epic** per campaign: its ID is the phase doc's `beads_epic`.
- One **child bead per row / sub-phase**, created with `--parent <epic>`. Its title starts with the row ID exactly as the phase doc writes it, then a space: `4.1b <short name>`.
- Find a row's bead with `bd children <epic> --json` and match the title prefix `<row-id> `. No other lookup table exists; the phase doc is not edited per row.

## Sync

A clone's beads database is local and gitignored. Claims reach other clones only through the Dolt remote. If `bd config get sync.remote` prints a remote:

- `bd dolt pull` before reading or claiming
- `bd dolt push` immediately after a claim, and at `/wrap` and `/end-session`

With no remote configured, skip both. Beads still works locally.

A campaign's "no push" rule (in its phase doc or its `/slash-goal`) covers **code**: git branches and tags. `bd dolt push` moves only the Dolt data ref (`refs/dolt/data`) and is not a code push, so it runs under a no-push campaign too. Keeping the Dolt data in the project's own origin (a separate ref from the code) is a supported setup.

## Operations (the session skills call these)

**Reconcile** (`/start-session`, silent). For each child of the epic that isn't closed:
- the row's closing commit exists (its subject carries the bead ID), or the campaign doc / a receipt marks the row closed → `bd close <id> --reason "<commit or receipt>" --actor ...`
- it is `in_progress` with an expired lease (`bd stale`) and no commit has touched the row since → `bd reclaim`
- a row in the phase doc has no bead → create it (`bd create --type=task --parent <epic> --title "<row-id> <name>" --actor ...`)

**Claim** (`/start-session`, and `/wrap` rolling on). Run pull → claim → push back to back, with nothing in between: `bd dolt pull`, `bd update <id> --claim --actor "<session-id>"`, `bd dolt push`.
- **Claim refused** because another actor holds it → that row is taken. Move to the next row the phase doc allows in parallel, or stop if there is none.
- **Push rejected** means another session pushed between your pull and your push. Run `bd dolt pull` and read its output. If it reports `auto-merged issue <your id>`, the claim is **contested**: Dolt settles it last-write-wins, so your local copy now shows you as holder even though the other session claimed it first. Treat the row as taken and **write nothing more to that bead**. Any write from you would make your stale claim the newest and overwrite theirs; the other session's next write (heartbeat or close) is newer and settles it everywhere. Move to the next row. If the pull reports no auto-merge of your bead, push again.
- Verified on bd 1.2.1 (2026-09-23): a sequential claim is refused across clones after a pull; a simultaneous claim is auto-merged last-write-wins, with the notice above.

**Progress** (`/checkpoint`). `bd note <id> "<done / left>" --actor ...` and `bd heartbeat <id> --actor ...`.

**Close** (`/wrap`, after the commit so the SHA exists). `bd close <id> --reason "<pass criterion met>; proof <test/capture>; commit <sha>" --actor ...`, then `bd dolt push`. Put the bead ID in the commit subject: `feat(4.1b): <summary> [<id>]`.

**File follow-ups** (`/end-session`). Each real piece of follow-up work from the devlog's *Issues Encountered* / *Next Steps* (not a lesson) becomes `bd create --type=task|bug --parent <epic> --title "<text>" --deps discovered-from:<current bead> --actor ...`. Lessons still go to `docs/lessons.md`.

**Phase boundary** (`/end-session` approving the phase). Close the epic: `bd close <epic> --reason "approved <date>" --actor ...`. bd refuses while children are open. Each open child either gets finished, is re-parented to the next campaign's epic, or stays open with its reason in the devlog line. Never `--force`.

**Release** (`/end-session` when a claimed row is being abandoned, not finished). `bd unclaim <id> --actor ...`.

## `/beads-mirror adopt [phase-doc]`: opt a formalized campaign in

**With no argument**, adopt the campaign this session is working on: the phase doc named by the active goal, the current focus in `docs/state.md`, or the latest devlog's `phase:`, in that order. Use the first source that names exactly one phase doc that exists. If none does, or if they disagree, stop and ask for the path. A placeholder such as `<phase-doc>` counts as no argument.

The phase doc is that campaign's file, so run this **inside the campaign's own session** when the campaign is entered and running. For an unentered campaign, any session may run it, provided no other live session holds the doc (check the project's held-files / lock convention). If another session holds it, stop and say so.

1. Check the activation preconditions (2) and (3). If they fail, report why and stop. This is the one beads operation the user asked for, so it reports.
2. If the doc already has `beads_epic`, run Reconcile and report the counts. Done.
3. `bd create --type=epic --title "<campaign name>" --external-ref "<phase-doc path>" --actor ...`
4. One child per row still in the phase doc's implementation order, titled `<row-id> <name>`. Rows the doc already records as closed are created and immediately closed with the commit or receipt that closed them, so the mirror is complete.
5. Add `beads_epic: <epic id>` to the phase doc's frontmatter. That line is the only edit to the doc.
6. `bd dolt push` if a remote is configured.
7. Commit only the frontmatter line: `docs(<campaign>): mirror rows into beads [<epic id>]`. Stage the phase doc path only.
8. Report: epic ID, rows created, rows closed on creation.

## Rules

- **The mirror never wins.** Git and the campaign doc decide; beads is corrected from them.
- **Opt-in only.** No `beads_epic`, no beads activity.
- **Silent.** Only the devlog line and `/beads-mirror adopt` ever say anything about beads.
- **Never `--force`, never `bd doctor --fix`, never `bd init`** from a session skill.
- **Per-session actor on every write.**
