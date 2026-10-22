from copy import deepcopy


ROUTE_VERSION = "0.3.0"

VALID_PRESETS = {
    "academic-method",
    "thesis-proposal",
    "engineering-system",
    "workflow-pipeline",
    "chinese-thesis-proposal",
    "chinese-grant-application",
    "academic-paper-framework-cn",
    "engineering-project-report-cn",
    "custom",
}

VALID_CONFIDENCE = {"high", "medium", "low"}

DOMAIN_CONTEXT_REQUIRED_FIELDS = [
    "discipline",
    "subfield",
    "project_type",
    "research_object",
    "method_family",
    "application_area",
]

DOMAIN_CONTEXT_RECOMMENDED_LIST_FIELDS = [
    "data_or_materials",
    "technical_objects",
    "domain_constraints",
    "evaluation_metrics",
    "expected_outputs",
]

UNKNOWN_DOMAIN_VALUES = {
    "",
    "unknown",
    "unspecified",
    "not specified",
    "not provided",
    "tbd",
    "todo",
    "n/a",
    "na",
}

SUPPORTED_FORMATS = [
    "pptx",
    "svg",
    "png",
    "drawio",
    "drawio-code",
    "excalidraw",
    "mermaid",
    "html",
    "markdown",
    "json",
]

PRESETS = {
    "academic-method": {
        "purpose": "Academic method framework",
        "outputs": ["pptx", "svg", "json"],
        "layout": "academic-method-framework",
        "style": "academic-blue",
        "source_type": "paper",
        "audience": "research",
    },
    "thesis-proposal": {
        "purpose": "Thesis/proposal technical route",
        "outputs": ["pptx", "svg", "drawio", "json"],
        "layout": "proposal-matrix-route",
        "style": "presentation-clean",
        "source_type": "proposal",
        "audience": "research",
    },
    "engineering-system": {
        "purpose": "Engineering system route",
        "outputs": ["pptx", "svg", "drawio", "html", "json"],
        "layout": "engineering-architecture-route",
        "style": "dark-technical",
        "source_type": "engineering",
        "audience": "engineering",
    },
    "workflow-pipeline": {
        "purpose": "Workflow or tool pipeline",
        "outputs": ["svg", "markdown", "mermaid", "json"],
        "layout": "horizontal-stages",
        "style": "minimal-gray",
        "source_type": "workflow",
        "audience": "technical",
    },
    "chinese-thesis-proposal": {
        "purpose": "Chinese thesis proposal poster route",
        "outputs": ["pptx", "svg", "drawio", "html", "json"],
        "layout": "cn-proposal-poster-route",
        "style": "cn-polished-pastel-academic",
        "source_type": "proposal",
        "audience": "research",
    },
    "chinese-grant-application": {
        "purpose": "Chinese grant or project application route",
        "outputs": ["pptx", "svg", "drawio", "html", "markdown", "json"],
        "layout": "cn-grant-application-route",
        "style": "cn-soft-grant-report",
        "source_type": "proposal",
        "audience": "research",
    },
    "academic-paper-framework-cn": {
        "purpose": "Chinese academic paper method framework",
        "outputs": ["pptx", "svg", "drawio", "json"],
        "layout": "cn-research-method-matrix",
        "style": "cn-blue-green-proposal",
        "source_type": "paper",
        "audience": "research",
    },
    "engineering-project-report-cn": {
        "purpose": "Chinese engineering project report route",
        "outputs": ["pptx", "svg", "drawio", "html", "json"],
        "layout": "cn-wide-project-map",
        "style": "cn-blue-green-proposal",
        "source_type": "engineering",
        "audience": "engineering",
    },
}


def has_domain_value(value):
    if isinstance(value, str):
        return value.strip().lower() not in UNKNOWN_DOMAIN_VALUES
    return value is not None


def has_domain_list(value):
    if not isinstance(value, list):
        return False
    return any(has_domain_value(item) for item in value)


def domain_context_missing_fields(route):
    context = route.get("domain_context")
    if not isinstance(context, dict):
        return DOMAIN_CONTEXT_REQUIRED_FIELDS + DOMAIN_CONTEXT_RECOMMENDED_LIST_FIELDS

    missing = []
    for field in DOMAIN_CONTEXT_REQUIRED_FIELDS:
        if not has_domain_value(context.get(field)):
            missing.append(field)
    for field in DOMAIN_CONTEXT_RECOMMENDED_LIST_FIELDS:
        if not has_domain_list(context.get(field)):
            missing.append(field)
    return missing


def domain_context_status(route):
    missing = domain_context_missing_fields(route)
    if not isinstance(route.get("domain_context"), dict):
        return "missing"
    return "complete" if not missing else "partial"


def selected_output_formats(route):
    metadata = route.get("metadata") or {}
    formats = metadata.get("selected_output_formats") or []
    return [str(item).lower() for item in formats]


def make_template_route(preset="academic-method"):
    if preset not in PRESETS:
        preset = "academic-method"
    config = PRESETS[preset]
    source_path = "source.md"
    route = {
        "route_version": ROUTE_VERSION,
        "title": "Project Technical Route",
        "subtitle": "Editable route generated by tech-route-maker",
        "selected_preset": preset,
        "layout": config["layout"],
        "style": config["style"],
        "domain_context": {
            "discipline": "unspecified",
            "subfield": "unspecified",
            "project_type": config["source_type"],
            "research_object": "unspecified",
            "method_family": "unspecified",
            "application_area": "unspecified",
            "data_or_materials": [],
            "technical_objects": [],
            "domain_constraints": [],
            "evaluation_metrics": [],
            "expected_outputs": [],
            "terminology": {},
            "domain_profile": {},
            "source": "template-placeholder",
            "confidence": "low",
        },
        "metadata": {
            "created_by": "tech-route-maker",
            "selected_output_formats": deepcopy(config["outputs"]),
            "source_type": config["source_type"],
            "source_files": [
                {
                    "id": "source_1",
                    "path": source_path,
                    "kind": "document",
                    "description": "Input source material",
                    "sha256": "",
                }
            ],
            "source_hashes": [],
            "language": "en",
            "audience": config["audience"],
        },
        "stages": [
            {
                "id": "objective",
                "title": "Objective",
                "order": 1,
                "nodes": [
                    {
                        "id": "objective_goal",
                        "label": "Define project goal",
                        "detail": "Clarify the problem and expected result.",
                        "tag": "objective",
                        "node_type": "objective",
                        "confidence": "high",
                        "is_inferred": False,
                        "evidence": [
                            {
                                "kind": "source",
                                "source_id": "source_1",
                                "path": source_path,
                                "locator": "Project goal",
                                "quote_or_note": "The source describes the project goal.",
                            }
                        ],
                    }
                ],
            },
            {
                "id": "input",
                "title": "Input Evidence",
                "order": 2,
                "nodes": [
                    {
                        "id": "input_source",
                        "label": "Collect source evidence",
                        "detail": "Gather documents, data, records, or repository evidence.",
                        "tag": "input",
                        "node_type": "input",
                        "confidence": "medium",
                        "is_inferred": False,
                        "evidence": [
                            {
                                "kind": "source",
                                "source_id": "source_1",
                                "path": source_path,
                                "locator": "Source materials",
                                "quote_or_note": "The source lists required materials.",
                            }
                        ],
                    }
                ],
            },
            {
                "id": "method",
                "title": "Method",
                "order": 3,
                "nodes": [
                    {
                        "id": "method_core",
                        "label": "Build core method",
                        "detail": "Transform input evidence into the core technical method.",
                        "tag": "method",
                        "node_type": "method",
                        "confidence": "medium",
                        "is_inferred": True,
                        "evidence": [],
                    }
                ],
            },
            {
                "id": "validation",
                "title": "Validation",
                "order": 4,
                "nodes": [
                    {
                        "id": "validation_check",
                        "label": "Validate route output",
                        "detail": "Check whether the method supports the expected result.",
                        "tag": "validation",
                        "node_type": "validation",
                        "confidence": "medium",
                        "is_inferred": True,
                        "evidence": [],
                    }
                ],
            },
        ],
        "edges": [
            {
                "id": "edge_1",
                "from": "objective_goal",
                "to": "input_source",
                "label": "guides",
                "kind": "flow",
                "confidence": "medium",
                "evidence": [],
            },
            {
                "id": "edge_2",
                "from": "input_source",
                "to": "method_core",
                "label": "feeds",
                "kind": "flow",
                "confidence": "medium",
                "evidence": [],
            },
            {
                "id": "edge_3",
                "from": "method_core",
                "to": "validation_check",
                "label": "validates",
                "kind": "flow",
                "confidence": "medium",
                "evidence": [],
            },
        ],
        "assumptions": [
            {
                "id": "assumption_1",
                "node_ids": ["method_core", "validation_check"],
                "text": "The initial route includes inferred method and validation nodes until source evidence is added.",
                "reason": "The template cannot know project-specific details before reading source material.",
                "impact": "medium",
            }
        ],
        "unresolved_questions": [
            {
                "id": "question_1",
                "text": "Which source file should be treated as authoritative?",
                "needed_input": "Provide the manuscript, proposal, engineering brief, or repository path.",
            },
            {
                "id": "question_2",
                "text": "Which discipline, subfield, project type, research object, method family, application area, constraints, and evaluation metrics should govern the route?",
                "needed_input": "Provide the project domain before rendering a final diagram.",
            }
        ],
        "quality_report": {},
        "citations": [],
        "renderer_overrides": {},
    }
    return route
