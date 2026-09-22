---
name: tier-check
description: Prove that delegation is real. Spawns a scout and a worker on a trivial task, then reads the runner's own transcripts to assert each ran on the cheap tier and the session on the frontier. Includes a negative control so the check is known to be able to fail. Run after installing the bundle, after changing agent definitions, or whenever a campaign's cost looks wrong.
allowed-tools: Agent, Read, Glob, Bash(python:*), Bash(date:*), Bash(powershell:*)
user-invocable: true
---

# Tier check

Delegation that is only declared is not delegation. This skill dispatches both cheap roles and then proves, from transcripts, which model each ran on.

## Step 1: Record the start time

Capture an ISO-8601 local timestamp before spawning anything (Bash: `date +%Y-%m-%dT%H:%M:%S`; PowerShell: `Get-Date -Format s`). Everything older is ignored.

## Step 2: Dispatch both roles

Spawn the two agents in one message so they run in parallel. Each prompt starts with its marker.

- **Claude Code**: `Agent` with `subagent_type: "scout"`, prompt `ROLE:scout Read README.md in the current directory and reply with its first heading only.` And `Agent` with `subagent_type: "worker"`, prompt `ROLE:worker Do not edit anything. Reply with the single word ok.`
- **Codex**: "spawn the `scout` agent with the prompt `ROLE:scout Read README.md and reply with its first heading only.`" and "spawn the `worker` agent with the prompt `ROLE:worker Do not edit anything. Reply with the single word ok.`"

Wait for both to return.

## Step 3: Assert from transcripts

Run the checker that ships with `/delegate` (path relative to that skill's base directory):

- Claude Code:
  `python <delegate base dir>/scripts/tier-check.py --runner claude --since <timestamp> --expect scout=claude-sonnet- --expect worker=claude-sonnet- --main claude-fable-`
- Codex:
  `python <delegate base dir>/scripts/tier-check.py --runner codex --since <timestamp> --expect scout=gpt-6-luna --expect worker=gpt-6-luna --main gpt-6-astra`

The `--main` prefix is whichever frontier model your session actually runs; check it rather than assuming, since the session model can change mid-run. The checker exits 0 only when both roles have a fresh transcript on the expected prefix and the session is on the frontier prefix; missing evidence is a FAIL.

## Step 4: Negative control

Run the same command once more with a wrong expectation, e.g. `--expect scout=claude-opus-` (Codex: `--expect scout=gpt-6-sol`). It must exit 1 and name the model it actually saw. If it passes, the checker is not reading the transcripts you think it is: stop and report that instead of a green result.

## Step 5: Report

```
Tier check: <PASS | FAIL>
  scout   ran on <models>   expected <prefix>
  worker  ran on <models>   expected <prefix>
  main    ran on <models>   expected <prefix>
  negative control: <failed as required | DID NOT FAIL>
```

A PASS with a negative control that did not fail is reported as FAIL.

## Rules

- Never claim a tier from an agent's self-description. Only the transcript counts.
- The negative control is mandatory. A check that cannot fail is a false green.
- Do not edit the agent definitions from this skill; report and let the user decide.
