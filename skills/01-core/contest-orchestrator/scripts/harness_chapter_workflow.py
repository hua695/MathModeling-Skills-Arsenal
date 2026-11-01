"""Validate chapter-approved writing without coupling progress to graphic repairs."""
from datetime import datetime
import hashlib
from pathlib import Path

import yaml


STAGES = {name: index for index, name in enumerate((
    "modeling", "validation", "evaluation", "conclusion", "analysis", "front_matter", "appendix", "abstract"))}
QUALITY = {"problem_answer", "model_and_derivation", "result_comparison", "interpretation", "continuity", "evidence_provenance"}


def validate(root, control, log, missing, failures, admission_only=False):
    root = Path(root).resolve()

    def time(value):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return result if result.tzinfo is not None else None
        except (AttributeError, TypeError, ValueError):
            return None

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def file(value, label, hashed=True):
        raw = value.get("path") if isinstance(value, dict) else value
        if not isinstance(raw, str) or Path(raw).is_absolute():
            missing.append(f"{label}: project-relative file required")
            return None
        path = (root / raw).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            missing.append(f"{label}: file missing or outside project")
            return None
        if hashed and (not isinstance(value, dict) or value.get("sha256") != digest(path)):
            failures.append(f"{label}: immutable source hash differs")
        return path

    def read(path):
        if path is None:
            return {}
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                return value
        except (OSError, ValueError, yaml.YAMLError) as error:
            failures.append(f"{path.name}: invalid mapping: {error}")
        return {}

    def approval(gate, packet_ref, required):
        packet_path = file(packet_ref, gate, hashed=False)
        packet = read(packet_path)
        entries = [a for a in log.get("approvals", []) if isinstance(a, dict) and a.get("gate") == gate]
        entry = entries[-1] if entries else {}
        at = time(entry.get("timestamp"))
        if entry.get("decision") != "approved" or at is None:
            missing.append(f"{gate}: actual human approval required")
            return None
        if not packet_path:
            return None
        if packet.get("node_id") != gate or packet.get("requested_decision") != "approve" or not packet.get("checks"):
            failures.append(f"{gate}: scoped review packet required")
        refs = packet.get("important_artifacts", [])
        hashes = {packet_path.relative_to(root).as_posix(): digest(packet_path)}
        if not isinstance(refs, list):
            failures.append(f"{gate}: artifact list required")
            refs = []
        for ref in refs:
            path = file(ref, gate)
            if path:
                hashes[path.relative_to(root).as_posix()] = digest(path)
        if any(path is not None and path.relative_to(root).as_posix() not in hashes for path in required):
            failures.append(f"{gate}: approval does not cover required chapter evidence")
        if entry.get("artifact_digests") != hashes:
            failures.append(f"{gate}: approval is stale")
        return at

    nodes = control.get("nodes", {})
    h7 = nodes.get("H7", {})
    prep = h7.get("writer_preparation")
    if not isinstance(prep, dict):
        missing.append("chapter_parallel: writer_preparation required")
        return
    h6 = next((a for a in reversed(log.get("approvals", [])) if isinstance(a, dict) and a.get("gate") == "H6"), {})
    h6_time = time(h6.get("timestamp"))
    if h6.get("decision") != "approved" or h6_time is None:
        missing.append("chapter_parallel: actual H6 approval required")
    plan_path = file(prep.get("writing_plan"), "writing_plan")
    plan = read(plan_path)
    plan_time = approval("H7_WRITING_PLAN", prep.get("plan_review_packet"), [plan_path])
    definitions = plan.get("chapters", [])
    order = plan.get("writing_order")
    print_order = plan.get("chapter_order")
    if (not isinstance(definitions, list) or any(not isinstance(c, dict) for c in definitions)
            or not isinstance(order, list) or not order or any(not isinstance(c, str) for c in order)
            or not isinstance(print_order, list) or any(not isinstance(c, str) for c in print_order)):
        failures.append("writing_plan: explicit chapter definitions, writing_order and chapter_order required")
        return
    by_id = {c.get("chapter_id"): c for c in definitions if isinstance(c.get("chapter_id"), str)}
    if len(by_id) != len(definitions) or len(set(order)) != len(order) or len(set(print_order)) != len(print_order) or set(order) != set(by_id) or set(print_order) != set(order):
        failures.append("writing_plan: writing and print orders must each cover every chapter exactly once")
        return
    if (not isinstance(plan.get("central_thesis"), str) or not plan["central_thesis"].strip()
            or not isinstance(plan.get("reader_journey"), list) or not plan["reader_journey"]):
        failures.append("writing_plan: evidence-bounded thesis and whole-paper reader journey required")
    ranks = [STAGES.get(by_id[c].get("kind"), -1) for c in order]
    if -1 in ranks or ranks != sorted(ranks) or not ranks or ranks[0] != STAGES["modeling"]:
        failures.append("writing_order: modeling first, evidence-dependent support later, abstract last")
    for chapter_id in order:
        chapter_definition = by_id[chapter_id]
        if not chapter_definition.get("reader_question") or not chapter_definition.get("expected_answer"):
            failures.append(f"{chapter_id}: reader question and intended chapter answer required")
        evidence = chapter_definition.get("evidence_refs")
        if not isinstance(evidence, list) or not evidence:
            failures.append(f"{chapter_id}: frozen evidence for the chapter argument required")
        else:
            for ref in evidence:
                file(ref, f"{chapter_id}.planned_evidence")
        dependencies = by_id[chapter_id].get("depends_on", [])
        if (not isinstance(dependencies, list) or any(not isinstance(d, str) or d not in order or order.index(d) >= order.index(chapter_id) for d in dependencies)):
            failures.append(f"{chapter_id}: dependency order is invalid")
    records = control.get("dispatch_records", [])
    if not isinstance(records, list):
        failures.append("chapter_parallel: actual dispatch list required")
        return
    writer_id = control.get("agent_instances", {}).get("H8", {}).get("agent_instance_id")
    route = control.get("agent_runtime_routes", {}).get("H8", {})
    used = set()

    def call(task_id, chapter_id, phase, after):
        matches = [r for r in records if isinstance(r, dict) and r.get("task_id") == task_id]
        if not isinstance(task_id, str) or not task_id or len(matches) != 1:
            failures.append(f"{chapter_id}: one actual {phase} dispatch required")
            return None
        r = matches[0]
        used.add(task_id)
        if (r.get("dispatch_kind") != "writer_preparation" or r.get("node_id") != "H8" or r.get("owner_role") != "论文 agent"
                or not writer_id or r.get("agent_instance_id") != writer_id
                or any(r.get(k) != route.get(k) for k in ("model", "reasoning_effort"))):
            failures.append(f"{chapter_id}: task must use the registered H8 writer/runtime")
        card_path = file({"path": r.get("task_card_path"), "sha256": r.get("task_card_sha256")}, task_id)
        card = read(card_path)
        scope = card.get("scope", {})
        if not isinstance(scope, dict) or scope.get("phase") != phase or scope.get("chapter_id") != chapter_id:
            failures.append(f"{task_id}: chapter-scoped writing task required")
        if any(card.get(k) != r.get(k) for k in ("task_id", "node_id", "owner_role", "model", "reasoning_effort")):
            failures.append(f"{task_id}: task identity mismatch")
        receipt = r.get("spawn_receipt")
        if not isinstance(receipt, dict) or any(receipt.get(k) != r.get(k) for k in ("task_id", "agent_instance_id", "task_card_sha256")):
            failures.append(f"{task_id}: genuine task receipt required")
        inputs = card.get("inputs", [])
        if not isinstance(inputs, list) or len(inputs) < 2 or prep.get("writing_plan") not in inputs:
            failures.append(f"{task_id}: approved plan and frozen scientific sources required")
        else:
            for ref in inputs:
                file(ref, f"{task_id}.input")
            planned_evidence = by_id.get(chapter_id, {}).get("evidence_refs", [])
            if any(ref not in inputs for ref in planned_evidence):
                failures.append(f"{task_id}: task must input this chapter's frozen scientific evidence")
        at = time(r.get("dispatched_at"))
        if at is None or after is None or at <= after:
            failures.append(f"{task_id}: dispatched before prerequisite human approval")
        if nodes.get("H8", {}).get("task_card") == r.get("task_card_path"):
            failures.append("formal H8 cannot be replaced by preliminary chapter writing")
        return at

    chapters = prep.get("chapters", [])
    if not isinstance(chapters, list) or any(not isinstance(c, dict) for c in chapters):
        failures.append("writer_preparation.chapters: list required")
        return
    expected = [c for c in order if by_id[c].get("kind") != "abstract"]
    started = []
    previous = max(h6_time, plan_time) if h6_time is not None and plan_time is not None else None
    revisions = {}
    latest = {}
    generation_tasks = {}
    draft_gates = {}
    chapter_approvals = {}
    for chapter in chapters:
        chapter_id = chapter.get("chapter_id")
        if not chapter.get("task_id"):
            continue
        if not isinstance(chapter_id, str) or chapter_id not in expected or chapter_id in started:
            failures.append("chapters: unique non-abstract writing units required")
            continue
        started.append(chapter_id)
        if started != expected[:len(started)]:
            failures.append(f"{chapter_id}: chapter dispatched outside approved writing order")
        draft_gates[chapter_id] = previous
        at = call(chapter.get("task_id"), chapter_id, "H8_chapter_draft", previous)
        draft = file(chapter.get("draft"), f"{chapter_id}.draft")
        completed = time(chapter.get("draft_completed_at"))
        if at is None or completed is None or completed <= at:
            failures.append(f"{chapter_id}: completion must follow chapter dispatch")
        quality_path = file(chapter.get("quality_review"), f"{chapter_id}.quality_review")
        quality = read(quality_path)
        checks = quality.get("checks", {})
        if quality.get("status") != "ready" or draft is None or quality.get("draft_sha256") != digest(draft) or not isinstance(checks, dict):
            failures.append(f"{chapter_id}: quality review must bind the complete chapter snapshot")
        else:
            for key in QUALITY:
                check = checks.get(key)
                if check != "PASS" and not (isinstance(check, dict) and check.get("status") == "not_applicable" and check.get("reason")):
                    failures.append(f"{chapter_id}: quality finding unresolved: {key}")
            if by_id[chapter_id].get("kind") == "modeling" and checks.get("model_and_derivation") != "PASS":
                failures.append(f"{chapter_id}: modeling chapter cannot omit its model and derivation")
        approved = approval(f"H7_CHAPTER:{chapter_id}", chapter.get("review_packet"), [draft, quality_path])
        if approved is not None and completed is not None and approved <= completed:
            failures.append(f"{chapter_id}: approval predates complete chapter")
        previous = approved
        chapter_approvals[chapter_id] = approved
        prompts = chapter.get("visual_prompts", [])
        if not isinstance(prompts, list) or any(not isinstance(p, dict) for p in prompts):
            failures.append(f"{chapter_id}: prompt revision list required")
            continue
        previous_revision = None
        for prompt in prompts:
            revision = prompt.get("revision_id")
            if not isinstance(revision, str) or not revision or (chapter_id, revision) in revisions or prompt.get("supersedes") != previous_revision:
                failures.append(f"{chapter_id}: immutable, explicitly linked prompt revisions required")
                continue
            called = call(prompt.get("task_id"), chapter_id, "H8_figure_prompt", approved)
            prompt_record = next((r for r in records if isinstance(r, dict) and r.get("task_id") == prompt.get("task_id")), {})
            prompt_card = read(file({"path": prompt_record.get("task_card_path"), "sha256": prompt_record.get("task_card_sha256")},
                                    f"{chapter_id}.{revision}.task"))
            if chapter.get("draft") not in prompt_card.get("inputs", []):
                failures.append(f"{chapter_id}: figure-prompt task must input the approved chapter snapshot")
            prepared = time(prompt.get("prepared_at"))
            if prepared is None or called is None or prepared <= called:
                failures.append(f"{chapter_id}: prompt output must follow authorized writer continuation")
            prompt_path = file(prompt.get("prompt"), f"{chapter_id}.{revision}.prompt")
            if prompt_path and not prompt_path.read_text(encoding="utf-8").strip():
                failures.append(f"{chapter_id}: self-contained figure prompt required")
            visual = read(file(prompt.get("visual_plan"), f"{chapter_id}.{revision}.visual_plan"))
            slots = visual.get("slots")
            if visual.get("draft") != chapter.get("draft") or visual.get("chapter_id") != chapter_id or visual.get("revision_id") != revision or not isinstance(slots, list) or not slots:
                failures.append(f"{chapter_id}: prompt must bind the approved draft and visual requirements")
            for slot in slots if isinstance(slots, list) else []:
                if not isinstance(slot, dict) or not isinstance(slot.get("slot_id"), str) or not slot["slot_id"]:
                    failures.append(f"{chapter_id}: concrete visual slot identifiers required")
                    continue
                representation = slot.get("representation")
                mode = representation.get("mode") if isinstance(representation, dict) else representation
                intent = slot.get("figure_intent", {})
                figure_route = slot.get("generation_route") or (intent.get("generation_route") if isinstance(intent, dict) else None)
                if mode not in ("figure", "table", "text") or (mode == "figure" and figure_route not in ("modelviz", "tikz-scientific-figures")):
                    failures.append(f"{chapter_id}: valid representation and scientific figure route required")
            revisions[chapter_id, revision] = (prompt, prepared, visual)
            latest[chapter_id] = revision
            previous_revision = revision
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("dispatch_kind") == "writer_preparation" and record.get("task_id") not in used:
            successor = next((r for r in records if isinstance(r, dict) and r.get("task_id") == record.get("superseded_by")
                              and r.get("task_id")), None)
            endpoint = successor
            history = {record.get("task_id")}
            while endpoint and endpoint.get("task_id") not in used:
                if (endpoint.get("task_id") in history or endpoint.get("dispatch_kind") != "writer_preparation"
                        or endpoint.get("node_id") != "H8" or endpoint.get("owner_role") != "论文 agent"
                        or endpoint.get("agent_instance_id") != writer_id
                        or any(endpoint.get(k) != route.get(k) for k in ("model", "reasoning_effort"))):
                    endpoint = None
                    break
                history.add(endpoint.get("task_id"))
                endpoint = next((r for r in records if isinstance(r, dict) and r.get("task_id") == endpoint.get("superseded_by")), None)
            if endpoint is None:
                successor = None
            old_card = read(file({"path": record.get("task_card_path"), "sha256": record.get("task_card_sha256")}, "superseded writer task"))
            new_card = read(file({"path": successor.get("task_card_path"), "sha256": successor.get("task_card_sha256")}, "successor writer task")) if successor else {}
            old_scope, new_scope = old_card.get("scope", {}), new_card.get("scope", {})
            cid = old_scope.get("chapter_id") if isinstance(old_scope, dict) else None
            phase = old_scope.get("phase") if isinstance(old_scope, dict) else None
            old_at, new_at = time(record.get("dispatched_at")), time(successor.get("dispatched_at")) if successor else None
            if (not successor or not record.get("superseded_reason") or not isinstance(new_scope, dict)
                    or phase not in ("H8_chapter_draft", "H8_figure_prompt")
                    or new_scope.get("chapter_id") != cid or new_scope.get("phase") != phase
                    or old_at is None or new_at is None or old_at >= new_at):
                failures.append("chapter_parallel: unbound writer dispatch needs a truthful same-chapter rework successor")
            else:
                call(record.get("task_id"), cid, phase, draft_gates.get(cid) if phase == "H8_chapter_draft" else chapter_approvals.get(cid))
        if record.get("node_id") != "H7":
            continue
        card = read(file({"path": record.get("task_card_path"), "sha256": record.get("task_card_sha256")}, "H7.task"))
        scope = card.get("scope", {})
        if not isinstance(scope, dict) or scope.get("phase") != "H7_generate":
            continue
        match = revisions.get((scope.get("chapter_id"), scope.get("revision_id")))
        if match is None:
            failures.append("H7: generation must bind a recorded approved-chapter prompt revision")
            continue
        prompt, prepared, visual = match
        if scope.get("prompt_sha256") != prompt.get("prompt", {}).get("sha256") or scope.get("approved_visual_plan_sha256") != prompt.get("visual_plan", {}).get("sha256"):
            failures.append("H7: generation prompt/visual-plan hashes differ")
        generated = time(record.get("dispatched_at"))
        if generated is None or prepared is None or generated <= prepared:
            failures.append("H7: generation cannot predate the chapter prompt")
        generation_tasks[record.get("task_id")] = (scope.get("chapter_id"), scope.get("revision_id"))
    closing = not admission_only and h7.get("status") in {"review_pending", "approved", "frozen"}
    if closing:
        if started != expected or previous is None:
            missing.append("H7 closure: all non-abstract writing units require chapter approval")
        for chapter in chapters:
            if chapter.get("chapter_id") in expected and not chapter.get("visual_prompts") and chapter.get("visuals_required") is not False:
                missing.append("H7 closure: each chapter needs a prompt or explicit no-visual decision")
        registry_path = file(h7.get("figure_registry"), "H7.figure_registry", hashed=False)
        registry = read(registry_path)
        assets = [registry_path]
        expected_slots = {}
        def slots_of(payload):
            slots = list(payload.get("slots", [])) if isinstance(payload.get("slots"), list) else []
            if isinstance(payload.get("global_visual_slots"), list):
                slots.extend(payload["global_visual_slots"])
            for question in payload.get("subproblems", []) if isinstance(payload.get("subproblems"), list) else []:
                if isinstance(question, dict) and isinstance(question.get("visual_audit"), list):
                    slots.extend(question["visual_audit"])
            result = {}
            for slot in slots:
                if not isinstance(slot, dict) or not isinstance(slot.get("slot_id"), str):
                    failures.append("H7 closure: explicit slot identifiers required")
                    continue
                if slot["slot_id"] in result:
                    failures.append("H7 closure: duplicate visual slot")
                result[slot["slot_id"]] = slot
            return result
        for chapter_id, revision in latest.items():
            for slot_id, slot in slots_of(revisions[chapter_id, revision][2]).items():
                if slot_id in expected_slots:
                    failures.append("H7 closure: two chapter prompts define the same slot")
                expected_slots[slot_id] = slot
        aggregate = read(file(h7.get("visual_argument_plan"), "H7.visual_argument_plan", hashed=False))
        if slots_of(aggregate) != expected_slots:
            failures.append("H7 closure: aggregate slots must match the latest writer prompts")
        for figure in registry.get("figures", []) if isinstance(registry.get("figures"), list) else []:
            if isinstance(figure, dict):
                chapter_id = figure.get("chapter_id")
                revision = figure.get("prompt_revision_id")
                if (not isinstance(chapter_id, str) or revision != latest.get(chapter_id)
                        or generation_tasks.get(figure.get("generation_task_id")) != (chapter_id, revision)):
                    failures.append("H7 closure: selected graphic must come from a real latest-revision generation task")
                for ext in ("svg", "png"):
                    ref = figure.get(ext)
                    assets.append(file(ref, f"H7.{ext}", hashed=isinstance(ref, dict)))
        selected = approval("H7_FIGURE_SELECTION", h7.get("figure_selection_review_packet"), assets)
        generated_times = [time(r.get("dispatched_at")) for r in records if isinstance(r, dict) and r.get("node_id") == "H7"]
        if selected is None or any(at is None or at >= selected for at in generated_times):
            failures.append("H7 closure: selected versions must follow figure work")
