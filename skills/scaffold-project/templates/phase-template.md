---
type: phase
status: planned
phase_number: __N__
prerequisite: __PREREQ__
estimated_effort: __EFFORT__
summary: __SUMMARY__
note_created: __DATE__
updated: __DATE__
---

# Phase __N__: __TITLE__

## Goal

One paragraph. What this phase accomplishes and why.

## Sub-phases

### __N__a: __TITLE__

**Deliverables**:
- [ ] __ITEM__

**Technical Details**:
Implementation specifics, API designs, code patterns.

**Verification**: How to test it works.

---

### __N__b: __TITLE__

**Deliverables**:
- [ ] __ITEM__

**Verification**: How to test it works.

## Key Files

| File | Status | Description |
|------|--------|-------------|
| `path/to/file` | New / Modify | What it does |

## Dependencies

- Library / SDK: __LIB__ version __VERSION__
- Prior phase: __PHASE__

## Autonomy & human-in-the-loop

- Human-intervention points: __LIST__
- Gate tiers: self-serve __LIST__ / conditional-proceed __LIST__ / hard-stop __LIST__
- Pre-authorizations: __LIST__

## Delegation

| Sub-phase | Delegable? | Allowed files | Test command | Retry budget |
|-----------|------------|---------------|--------------|--------------|
| __N__a | delegable / judge-only | `path/one`, `path/two` | `__CMD__` | 2 |
| __N__b | delegable / judge-only | | | |

## Success Criteria

- [ ] Testable criterion
- [ ] Testable criterion

## References

- Spec: `docs/design/spec.md` §__SECTION__
- Research: `docs/research_results/__TOPIC__.md`
- Related playbook: `<global-playbooks>/__SLUG__.md`
