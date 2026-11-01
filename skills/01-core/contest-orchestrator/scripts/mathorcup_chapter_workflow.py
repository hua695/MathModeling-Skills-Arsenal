"""MathorCup chapter approval and asynchronous figure revision checks."""
from datetime import datetime


STAGES = {name: index for index, name in enumerate((
    "modeling", "validation", "evaluation", "conclusion", "analysis", "front_matter", "appendix", "abstract"))}
PROSE_CHECKS = {"language_profile_terms", "first_use_symbol_definitions", "claim_evidence_coverage", "metadiscourse", "negative_echo"}
ARGUMENT_CHECKS = {"problem_answer", "model_and_derivation", "result_comparison", "interpretation", "continuity", "evidence_provenance"}


def validate(root, control, log, ids, times, reviewed, errors, pauses, core, final=False):
    """Reuse native MathorCup artifact, approval and dispatch contracts."""
    m4 = control["nodes"]["M4"]

    def artifact(ref, label):
        return core._artifact(root, ref, label, errors)

    def load(ref, label):
        found = artifact(ref, label)
        return core._read(found[1], errors) if found else {}

    def review(gate, ref, required, exact=False):
        if not ref:
            pauses.append(f"{gate}: review packet not ready")
            return None
        found = [value for value in (artifact(r, gate) for r in required) if value]
        at, hashes = core._review(root, control, log, gate, ref, found, errors, pauses)
        events = [a for a in log.get("approvals", []) if isinstance(a, dict) and a.get("gate") == gate]
        if not events or events[-1].get("decision") != "approve" or events[-1].get("approved_by") != "user":
            pauses.append(f"{gate}: latest decision is not human approval")
            at = None
        reviewed.setdefault("M4", {}).update(hashes)
        packet = load(ref, gate)
        if packet.get("requested_decision") != "approve":
            errors.append(f"{gate}: explicit approval request required")
        if exact and packet.get("important_artifacts") != required:
            errors.append(f"{gate}: chapter approval binds only immutable prose and its quality report")
        # Chapter decisions require actual approval of completed prose, not a
        # replay-wide date standing in for a per-chapter decision.
        if not isinstance(at, datetime):
            if at is not None:
                errors.append(f"{gate}: timestamped human approval required")
            return None
        times[gate] = at
        return at

    plan = load(m4.get("paper_argument_blueprint"), "M4.paper_argument_blueprint")
    global_plan = plan.get("global", {})
    definitions = plan.get("chapters", [])
    order = global_plan.get("writing_order") if isinstance(global_plan, dict) else None
    print_order = global_plan.get("chapter_order") if isinstance(global_plan, dict) else None
    if (not isinstance(definitions, list) or any(not isinstance(c, dict) for c in definitions)
            or not isinstance(order, list) or not order or any(not isinstance(c, str) for c in order)
            or not isinstance(print_order, list) or any(not isinstance(c, str) for c in print_order)):
        errors.append("M4: explicit chapter definitions, writing_order and chapter_order required")
        return
    by_id = {c["chapter_id"]: c for c in definitions if isinstance(c.get("chapter_id"), str)}
    if (len(by_id) != len(definitions) or len(set(order)) != len(order)
            or len(set(print_order)) != len(print_order) or set(order) != set(by_id) or set(print_order) != set(order)):
        errors.append("M4: both chapter orders must cover every chapter exactly once")
        return
    ranks = [STAGES.get(by_id[c].get("kind"), -1) for c in order]
    if (-1 in ranks or ranks != sorted(ranks) or ranks[0] != STAGES["modeling"]
            or ranks.count(STAGES["abstract"]) != 1 or ranks[-1] != STAGES["abstract"]):
        errors.append("M4: writing_order must start with modeling and finish with one abstract")
    if not global_plan.get("central_thesis") or not global_plan.get("reader_journey"):
        errors.append("M4: whole-paper thesis and reader journey required")
    for chapter_id in order:
        definition = by_id[chapter_id]
        dependencies = definition.get("depends_on", [])
        if (not isinstance(dependencies, list) or any(not isinstance(d, str) or d not in order
                or order.index(d) >= order.index(chapter_id) for d in dependencies)):
            errors.append(f"{chapter_id}: dependency order invalid")
        evidence = definition.get("evidence_refs")
        if not isinstance(evidence, list) or not evidence or not definition.get("reader_question") or not definition.get("expected_answer"):
            errors.append(f"{chapter_id}: chapter argument and frozen evidence required")
        for ref in evidence if isinstance(evidence, list) else []:
            artifact(ref, f"{chapter_id}.planned_evidence")

    records = control.get("dispatch_records", [])
    tasks = {}
    for record in records if isinstance(records, list) else []:
        if isinstance(record, dict) and record.get("node_id") == "M4":
            tasks.setdefault(record.get("task_id"), []).append(record)
    used = {}
    base_inputs = [m4.get(key) for key in ("paper_argument_blueprint", "paper_language_profile", "paper_material_readiness", "paper_claim_coverage")]

    def call(task_id, role, phase, chapter_id, required, after, revision_id=None, remember=True):
        matches = tasks.get(task_id, []) if isinstance(task_id, str) else []
        if len(matches) != 1:
            errors.append(f"{chapter_id or phase}: one actual {phase} dispatch required")
            return None
        record = matches[0]
        card = load({"path": record.get("task_card"), "sha256": record.get("task_card_sha256")}, str(task_id))
        scope = card.get("scope", {})
        expected = {"task_id": task_id, "node_id": "M4", "owner_role": role,
                    "agent_instance_id": ids.get(role), "model": core.ROUTES[role][0], "reasoning_effort": core.ROUTES[role][1]}
        if any(record.get(key) != value or card.get(key) != value for key, value in expected.items()):
            errors.append(f"{task_id}: registered M4 role and actual task identity required")
        if (not isinstance(scope, dict) or scope.get("phase") != phase
                or scope.get("chapter_id") != chapter_id
                or (revision_id is not None and scope.get("revision_id") != revision_id)):
            errors.append(f"{task_id}: task chapter, phase or revision mismatch")
        at = core._time(record.get("called_at"))
        if not isinstance(at, datetime) or not core._gate_was_satisfied_before(at, after):
            errors.append(f"{task_id}: dispatch precedes its required approval or source")
        inputs = card.get("inputs", [])
        if not isinstance(inputs, list) or any(not isinstance(ref, dict) or ref not in inputs for ref in required):
            errors.append(f"{task_id}: approved prose, plan or frozen evidence input missing")
        if remember:
            used[task_id] = (role, phase, chapter_id, required, after, revision_id)
        return at

    def quality(chapter_id, chapter):
        report_ref = chapter.get("quality_review")
        report = load(report_ref, f"{chapter_id}.quality_review")
        draft = chapter.get("draft")
        if report.get("status") != "ready" or not isinstance(draft, dict) or report.get("draft_sha256") != draft.get("sha256"):
            errors.append(f"{chapter_id}: quality report must bind the complete chapter draft")
        checks = report.get("checks", {})
        for name in ARGUMENT_CHECKS | PROSE_CHECKS:
            status = checks.get(name) if isinstance(checks, dict) else None
            allowed_na = (name not in PROSE_CHECKS and name != "evidence_provenance"
                          and not (name == "model_and_derivation" and by_id[chapter_id].get("kind") == "modeling"))
            if status != "PASS" and not (allowed_na and isinstance(status, dict)
                    and status.get("status") == "not_applicable" and status.get("reason")):
                errors.append(f"{chapter_id}: quality check {name} must pass or have a justified non-applicability")
        review_call(report_ref, chapter_id)

    def review_call(ref, label):
        calls = m4.get("skill_invocations", [])
        calls = calls if isinstance(calls, list) else []
        if not isinstance(ref, dict) or not any(isinstance(c, dict) and c.get("skill") == "论文辅助"
                and c.get("status") == "completed" and c.get("evidence_ref") == ref.get("path")
                and c.get("evidence_sha256") == ref.get("sha256") for c in calls if isinstance(calls, list)):
            errors.append(f"{label}: actual read-only 论文辅助 invocation must bind its review evidence")

    chapters = m4.get("writing_chapters", [])
    if (not isinstance(chapters, list) or any(not isinstance(c, dict) for c in chapters)
            or [c.get("chapter_id") for c in chapters] != order[:len(chapters)]):
        errors.append("M4: writing_chapters must be a unique prefix of writing_order")
        return
    plan_time = times.get("M4_WRITING_PLAN")
    previous = plan_time
    drafts, latest, selected, selection_times = [], {}, {}, []
    all_body_approved = len(chapters) >= len(order) - 1
    for index, chapter in enumerate(chapters):
        chapter_id = chapter["chapter_id"]
        is_abstract = by_id[chapter_id].get("kind") == "abstract"
        if is_abstract:
            framework = m4.get("abstract_framework")
            framework_at = call(m4.get("abstract_framework_task_id"), "writer", "abstract_framework", None,
                                [*base_inputs, *drafts], previous)
            framework_time = review("M4_ABSTRACT_FRAMEWORK", m4.get("abstract_framework_review_packet"), [framework])
            if framework_at is not None and (framework_time is None or framework_time <= framework_at):
                errors.append("M4: abstract framework approval must follow its author discussion")
            previous = framework_time
        evidence = by_id[chapter_id].get("evidence_refs", [])
        required = [*base_inputs, *drafts, *(evidence if isinstance(evidence, list) else [])]
        if is_abstract:
            required.append(m4.get("abstract_framework"))
        draft_time = call(chapter.get("task_id"), "writer", "draft", chapter_id, required, previous)
        draft = chapter.get("draft")
        draft_file = artifact(draft, f"{chapter_id}.draft")
        if draft_file and not draft_file[1].read_text(encoding="utf-8").strip():
            errors.append(f"{chapter_id}: complete nonempty chapter required")
        completed = core._time(chapter.get("draft_completed_at"))
        if completed is None or draft_time is None or completed <= draft_time:
            errors.append(f"{chapter_id}: draft completion must follow its actual writer call")
        quality(chapter_id, chapter)
        packet_ref = chapter.get("review_packet")
        approved = review(f"M4_CHAPTER:{chapter_id}", packet_ref, [draft, chapter.get("quality_review")], exact=True)
        if approved is not None and (completed is None or approved <= completed):
            errors.append(f"{chapter_id}: approval must follow completed prose")
        if approved is None and not is_abstract:
            all_body_approved = False
        if packet_ref:
            packet = load(packet_ref, f"{chapter_id}.review_packet")
            if packet.get("review_type") != "paper_chapter_review" or packet.get("reviewer_skill") != "论文辅助":
                errors.append(f"{chapter_id}: scoped paper_chapter_review required")
        previous = approved
        drafts.append(draft)
        prompts = chapter.get("visual_prompts", [])
        if not isinstance(prompts, list) or any(not isinstance(p, dict) for p in prompts):
            errors.append(f"{chapter_id}: visual_prompts list required")
            prompts = []
        if not prompts:
            if final and chapter.get("visuals_required") is not False:
                errors.append(f"{chapter_id}: final chapter needs prompts or explicit visuals_required:false")
            continue
        if chapter.get("visuals_required") is False:
            errors.append(f"{chapter_id}: no-visual declaration conflicts with prompts")
        prior_revision, prior_prepared, seen = None, None, set()
        for revision in prompts:
            rid = revision.get("revision_id")
            if not isinstance(rid, str) or not rid or rid in seen or revision.get("supersedes") != prior_revision:
                errors.append(f"{chapter_id}: immutable prompt revision chain invalid")
            seen.add(rid) if isinstance(rid, str) else None
            prior_revision = rid
            prompt_time = call(revision.get("task_id"), "writer", "figure_prompt", chapter_id,
                               [*base_inputs, draft, *(evidence if isinstance(evidence, list) else [])], approved, rid)
            prompt_file = artifact(revision.get("prompt"), f"{chapter_id}.{rid}.prompt")
            prepared = core._time(revision.get("prepared_at"))
            if prepared is None or prompt_time is None or prepared <= prompt_time:
                errors.append(f"{chapter_id}.{rid}: prompt must follow its actual writer call")
            if prior_prepared is not None and (prompt_time is None or prompt_time <= prior_prepared):
                errors.append(f"{chapter_id}.{rid}: revised prompt call must follow the previous revision")
            prior_prepared = prepared
            if prompt_file and not prompt_file[1].read_text(encoding="utf-8").strip():
                errors.append(f"{chapter_id}.{rid}: self-contained prompt required")
            visual_plan = load(revision.get("visual_plan"), f"{chapter_id}.{rid}.visual_plan")
            slots = visual_plan.get("slots")
            if (visual_plan.get("owner_role") != "writer" or visual_plan.get("chapter_id") != chapter_id
                    or visual_plan.get("revision_id") != rid or visual_plan.get("draft") != draft
                    or not isinstance(slots, list) or not slots or any(not isinstance(s, dict) for s in slots)):
                errors.append(f"{chapter_id}.{rid}: writer plan must bind approved prose and nonempty slots")
                slots = []
            for slot in slots:
                if (not slot.get("slot_id") or slot.get("representation") not in {"figure", "table", "text"}
                        or not all(slot.get(key) for key in ("reader_question", "body_anchor", "claim", "evidence_refs"))):
                    errors.append(f"{chapter_id}.{rid}: complete named visual need required")
                if slot.get("representation") == "figure" and slot.get("generation_route") not in {"modelviz", "tikz-scientific-figures"}:
                    errors.append(f"{chapter_id}.{rid}: supported figure route required")
                for ref in slot.get("evidence_refs", []) if isinstance(slot.get("evidence_refs"), list) else []:
                    artifact(ref, f"{chapter_id}.{rid}.slot_evidence")
            generation_time = None
            if revision.get("generation_task_id"):
                generation_time = call(revision["generation_task_id"], "figure", "generate", chapter_id,
                                       [draft, revision.get("prompt"), revision.get("visual_plan")], prepared, rid)
            latest[chapter_id] = (revision, slots, generation_time)

    if len(chapters) == len(order) - 1 and m4.get("abstract_framework_task_id"):
        framework_at = call(m4["abstract_framework_task_id"], "writer", "abstract_framework", None,
                            [*base_inputs, *drafts], previous)
        framework_time = review("M4_ABSTRACT_FRAMEWORK", m4.get("abstract_framework_review_packet"), [m4.get("abstract_framework")])
        if framework_time is not None and (framework_at is None or framework_time <= framework_at):
            errors.append("M4: abstract framework approval must follow its author discussion")

    # In-flight graphic work never becomes a draft-admission prerequisite.
    if final or m4.get("integration_task_id"):
        if len(chapters) != len(order) or previous is None:
            pauses.append("M4: all chapters including abstract require approval before final integration")
        aggregate = load(m4.get("visual_argument_plan"), "M4.visual_argument_plan")
        expected_slots = [slot for _, slots, _ in latest.values() for slot in slots]
        actual_slots, _ = core._modern_visual_slots(aggregate)
        def slot_map(slots):
            result = {}
            for slot in slots if isinstance(slots, list) else []:
                if not isinstance(slot, dict) or not isinstance(slot.get("slot_id"), str) or slot["slot_id"] in result:
                    errors.append("M4: unique aggregate visual slot IDs required")
                    continue
                result[slot["slot_id"]] = slot
            return result
        if slot_map(actual_slots) != slot_map(expected_slots):
            errors.append("M4: final visual plan must equal latest chapter prompt plans")
        registry = load(m4.get("figure_registry"), "M4.figure_registry")
        figures = registry.get("figures", [])
        for chapter_id, (revision, slots, generated) in latest.items():
            expected_figures = {s.get("slot_id") for s in slots if s.get("representation") == "figure"}
            if not expected_figures:
                continue
            if generated is None:
                errors.append(f"{chapter_id}: latest prompt has no actual figure generation")
            selection_ref = revision.get("figure_selection")
            selection = load(selection_ref, f"{chapter_id}.figure_selection")
            assets = selection.get("assets", [])
            if (selection.get("chapter_id") != chapter_id or selection.get("revision_id") != revision.get("revision_id")
                    or not isinstance(assets, list) or any(not isinstance(a, dict) for a in assets)
                    or {a.get("slot_id") for a in assets} != expected_figures or len(assets) != len(expected_figures)):
                errors.append(f"{chapter_id}: selected assets must cover exactly the latest requested figure slots")
                assets = []
            bound_assets = [selection_ref]
            for asset in assets:
                selected[asset["slot_id"]] = asset
                bound_assets.append({"path": asset.get("path"), "sha256": asset.get("sha256")})
            matching = [f for f in figures if isinstance(f, dict) and f.get("chapter_id") == chapter_id] if isinstance(figures, list) else []
            for figure in matching:
                if (figure.get("prompt_revision_id") != revision.get("revision_id")
                        or figure.get("generation_task_id") != revision.get("generation_task_id")):
                    errors.append(f"{chapter_id}: final figure must bind latest prompt and actual generation")
                for kind in ("svg", "png"):
                    bound_assets.append({"path": figure.get(kind), "sha256": figure.get(f"{kind}_sha256")})
                for slot in figure.get("visual_slot_ids", []):
                    chosen = selected.get(slot, {})
                    if figure.get("selected_asset") != {"path": chosen.get("path"), "sha256": chosen.get("sha256")} or figure.get("svg") != chosen.get("path"):
                        errors.append(f"{chapter_id}: registry differs from selected SVG")
            chosen_at = review(f"M4_FIGURE_SELECTION:{chapter_id}:{revision.get('revision_id')}",
                               revision.get("figure_selection_review_packet"), bound_assets)
            if chosen_at is not None:
                selection_times.append(chosen_at)
                if generated is None or chosen_at <= generated:
                    errors.append(f"{chapter_id}: selected assets must follow latest generation")
        for figure in figures if isinstance(figures, list) else []:
            if isinstance(figure, dict) and figure.get("chapter_id") not in latest:
                errors.append("M4: every registered figure must belong to a latest chapter prompt")
        required = [*base_inputs, *drafts, m4.get("abstract_framework"), m4.get("visual_argument_plan"), m4.get("figure_registry")]
        required.extend({"path": a.get("path"), "sha256": a.get("sha256")} for a in selected.values())
        integration_time = call(m4.get("integration_task_id"), "writer", "write", None, required,
                                max([previous, *selection_times]) if isinstance(previous, datetime) else None)
        manuscript = m4.get("final_manuscript")
        final_time = review("M4_FINAL_PAPER", m4.get("final_review_packet"), [manuscript, m4.get("paper_pdf"), *drafts, m4.get("figure_registry"), m4.get("visual_argument_plan")])
        final_packet = load(m4.get("final_review_packet"), "M4.final_review_packet")
        statuses = {c.get("id", c.get("name")): c.get("status") for c in final_packet.get("checks", []) if isinstance(c, dict)}
        if (final_packet.get("review_type") != "paper_final_review" or final_packet.get("reviewer_skill") != "论文辅助"
                or any(statuses.get(name) != "PASS" for name in PROSE_CHECKS | {"abstract_contract", "whole_paper_final"})):
            errors.append("M4: complete read-only final paper review required")
        review_call(m4.get("final_review_packet"), "M4_FINAL_PAPER")
        if final_time is not None and (integration_time is None or final_time <= integration_time):
            errors.append("M4: final paper approval must follow actual integration")

    # Check all actual calls, including retries; no unbound writer work can hide
    # behind a superseded_by pointer or a cross-role intermediate task.
    for task_id, matches in tasks.items():
        for record in matches:
            if record.get("owner_role") not in {"writer", "figure"}:
                continue
            card = load({"path": record.get("task_card"), "sha256": record.get("task_card_sha256")}, str(task_id))
            if card.get("scope", {}).get("phase") == "plan":
                continue
            if task_id in used:
                if record.get("superseded_by"):
                    errors.append(f"{task_id}: current accepted task cannot be superseded")
                continue
            visited, endpoint = set(), record
            while endpoint and endpoint.get("task_id") not in used:
                successor = endpoint.get("superseded_by")
                if endpoint.get("task_id") in visited or not endpoint.get("superseded_reason") or len(tasks.get(successor, [])) != 1:
                    endpoint = None
                    break
                visited.add(endpoint.get("task_id"))
                next_record = tasks[successor][0]
                old_scope = load({"path": endpoint.get("task_card"), "sha256": endpoint.get("task_card_sha256")}, str(task_id)).get("scope", {})
                new_scope = load({"path": next_record.get("task_card"), "sha256": next_record.get("task_card_sha256")}, str(successor)).get("scope", {})
                old_time, new_time = core._time(endpoint.get("called_at")), core._time(next_record.get("called_at"))
                if (any(endpoint.get(k) != next_record.get(k) for k in ("owner_role", "agent_instance_id", "model", "reasoning_effort"))
                        or any(old_scope.get(k) != new_scope.get(k) for k in ("phase", "chapter_id", "revision_id"))
                        or old_scope.get("phase") not in {"draft", "figure_prompt"}
                        or old_time is None or new_time is None or new_time <= old_time):
                    endpoint = None
                    break
                endpoint = next_record
            if endpoint is None or endpoint.get("task_id") not in used:
                errors.append(f"{task_id}: unbound chapter dispatch or invalid retry chain")
                continue
            role, phase, cid, required, after, rid = used[endpoint["task_id"]]
            call(task_id, role, phase, cid, required, after, rid, remember=False)

    if not all_body_approved and m4.get("abstract_framework_task_id"):
        errors.append("M4: abstract framework requires approval of every body and appendix chapter")
