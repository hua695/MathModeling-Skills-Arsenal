# Paper Spine and Chapter Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the H8 paper workflow enforce one global argument spine, explicit chapter dependencies, and modeling/solving as the paper's core chapters.

**Architecture:** Extend the H4 narrative blueprint with an authoritative chapter spine. Propagate the spine into the H8 argument blueprint, author brief, chapter writing card, and continuity context. Add deterministic checks for chapter roles, order, adjacent handoffs, and consistency across these artifacts; keep the existing single H8 writer agent and user approval gates.

**Tech Stack:** Python 3, `unittest`, PyYAML, Markdown/YAML templates, LaTeX narrative checker.

**Spec:** `SKILL.md` H8 writing contract and `references/h8_writer_first_protocol.md`.

## Global Constraints

- Modify only `contest-orchestrator`.
- Keep version `4.18` and preserve `full-contest-legacy` as the v4.16 compatibility baseline.
- Do not create additional mandatory paper agents.
- Core chapters are the modeling and solving chapters; support chapters prepare, connect, or synthesize evidence.
- No internal process language enters paper artifacts.
- Write failing tests before implementation changes and run the full regression suite before completion.

---

### Task 1: Add failing spine-contract tests

**Files:**
- Modify: `tests/test_harness_control.py`
- Modify: `tests/test_authoring_architecture.py`
- Modify: `tests/test_paper_narrative.py`

**Interfaces:**
- Tests call the existing checker helpers and assert the new `paper_spine` and chapter-handoff fields are required and consistent.

- [ ] **Step 1: Write failing tests**

Add tests for:

1. A narrative blueprint without `global.paper_spine` is rejected at H5/H6.
2. A spine whose `chapter_order` has no adjacent edge is rejected.
3. An approved author brief without `chapter_role`, `reads_from`, `feeds_to`, or `handoff_question` is rejected.
4. A chapter card whose handoff fields disagree with the author brief is rejected.
5. A continuity context whose current chapter is not in the spine is rejected.
6. A LaTeX paper with an isolated narrative chapter is reported by the narrative checker.
7. A valid core/support chapter chain is accepted.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```text
python -m unittest tests.test_harness_control tests.test_authoring_architecture tests.test_paper_narrative
```

Expected: the new assertions fail because the current templates and checker do not require or validate chapter-spine fields.

---

### Task 2: Implement the authoritative paper spine

**Files:**
- Modify: `scripts/check_harness_control.py`
- Modify: `scripts/check_paper_narrative.py`

**Interfaces:**
- Add a shared checker helper that validates `core_chapters`, `support_chapters`, `chapter_order`, and `chapter_edges`.
- H5/H6 narrative validation consumes `narrative.global.paper_spine`.
- H8 blueprint, author brief, chapter card, and continuity validation consume the same normalized spine.

- [ ] **Step 1: Add spine validation rules**

Require:

- nonempty `core_chapters` and `chapter_order`;
- disjoint `core_chapters` and `support_chapters`;
- every declared chapter appears exactly once in `chapter_order`;
- every modeling question in `narrative` appears in `core_chapters`;
- every adjacent pair in `chapter_order` has exactly one nonempty edge with `relation` and `handoff_question`;
- no self-edge or duplicate edge.

- [ ] **Step 2: Bind H8 artifacts to the spine**

Require each chapter entry to declare `chapter_role`, `reads_from`, `feeds_to`, `new_claims_allowed`, and `handoff_question`. Verify roles, order, immediate predecessor/successor, and handoff text against the authoritative spine. Require core chapters to carry arguments and model structure; support chapters cannot introduce unbound new claims.

- [ ] **Step 3: Add full-paper orphan and dependency checks**

Extend the LaTeX narrative checker with a deterministic report for core/support chapter coverage and obvious isolated chapter headings. Keep the result as a quality warning for ordinary paper checks; H8 control validation remains the hard artifact gate.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the focused test command from Task 1. Expected: all new tests pass.

---

### Task 3: Update H8 templates and operational guidance

**Files:**
- Modify: `templates/paper_narrative.yaml`
- Modify: `templates/paper_argument_blueprint.yaml`
- Modify: `templates/paper_author_brief.yaml`
- Modify: `templates/chapter_writing_card.yaml`
- Modify: `templates/paper_continuity_context.yaml`
- Modify: matching files under `templates/b_project_template/`
- Modify: `references/h8_writer_first_protocol.md`
- Modify: `references/h8_chapter_execution.md`
- Modify: `SKILL.md`

**Interfaces:**
- Templates expose the fields consumed by Task 2 without adding a new agent or a new node.
- H8 writer guidance treats modeling/solving as the central spine and uses chapter handoff fields before drafting.

- [ ] **Step 1: Add final-only template fields**

Add `paper_spine` to the narrative and argument blueprint templates, and add chapter-role and handoff fields to the author brief, chapter card, and continuity context. Keep placeholders operational and free of process history.

- [ ] **Step 2: Document the reader-first chapter contract**

State that support chapters prepare or synthesize evidence for the core modeling/solving chapters. Require each chapter opening to answer its reader question and each ending to hand off the next question using domain logic rather than workflow narration.

- [ ] **Step 3: Run template parsing and focused tests**

Run the focused tests and parse every changed YAML template with PyYAML.

---

### Task 4: Regression, replay, and release checks

**Files:**
- Modify only test fixtures if existing tests require the new mandatory fields.

**Interfaces:**
- Existing H0–H9, appendix, figure, literature, delivery, and replay contracts remain unchanged except for the new H8 spine fields.

- [ ] **Step 1: Run focused regression**

```text
python -m unittest tests.test_harness_control tests.test_authoring_architecture tests.test_paper_narrative
```

- [ ] **Step 2: Run full validation**

```text
python -m compileall -q scripts tests planner memory
python -m unittest discover -s tests -p "test_*.py"
python scripts/skill_health_check.py . --strict --smoke
python -X utf8 C:/Users/USER/.codex/skills/.system/scripts/quick_validate.py .
python scripts/replay_profiles.py --strict
```

- [ ] **Step 3: Confirm scope and artifact hygiene**

Run `git diff --check` and verify that all changes are inside `contest-orchestrator`; no internal discussion or discarded content appears in runtime templates or deliverable-facing guidance.

