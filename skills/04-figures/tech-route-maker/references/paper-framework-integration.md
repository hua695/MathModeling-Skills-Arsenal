# Paper Framework Integration

This reference integrates transferable rules from `c-narcissus/paper-framework-figure-studio-pro` after reading its README, SKILL.md, templates, and key references. The source repository declares MIT-0 in its README. This file adapts concepts for `tech-route-maker`; it does not vendor the original large image/icon assets.

## What to adopt

### Source foundation before figure design

For academic inputs, build a source-grounded foundation before drawing:

- problem, gap, assumptions, and objective;
- ordered method or algorithm steps;
- architecture, modules, components, training flow, inference flow, and inputs/outputs;
- losses, objectives, equations, constraints, variables, metrics, and terminology mapping;
- artifact lineage for generated data, memory, retrieval results, pseudo-labels, prototypes, scores, weights, teacher signals, validation proxies, rewards, or intermediate states;
- arrow semantics with source, target, meaning, and evidence;
- figure-relevant inclusions, exclusions, uncertainty, reviewer risks, and non-droppable core substeps.

For legacy campaign inputs, build the equivalent foundation only when the user explicitly asks for advertising or campaign work:

- brand or campaign objective, target audience, insight, promise, and constraints;
- creative strategy, content/message route, channel route, production route, approval route, and conversion/evaluation route;
- deliverables, timeline, evidence, assumptions, and risks.

### Figure subtype routing

Ask the user to choose one figure purpose/subtype. Recommended menu:

- `academic_method_framework`
- `paper_architecture_overview`
- `pipeline_process`
- `agent_tool_workflow`
- `system_data_flow`
- `mechanism_intuition`
- `case_walkthrough`
- `evidence_linked_framework`
- `failure_aware_framework`
- `thesis_proposal_technical_route`
- `legacy_advertising_strategy_route`
- `legacy_campaign_production_workflow`
- `legacy_customer_journey_funnel`
- `media_channel_swimlane`

Use multi-label reasoning internally, but render from the selected primary subtype.

### Reader-first route

Every diagram should have a `reader_question` and a `reader_path` of 3 to 7 anchor steps. If the reader path is not obvious, simplify the diagram before rendering.

Examples:

- "What is the proposed method and why are these parts organized this way?"
- "Which modules interact during training and inference?"
- "How does one example move through the framework?"
- "How does the legacy campaign move from audience insight to conversion?"

### Semantic graph versus visual graph

Keep a complete semantic/audit graph in `tech-route.json`, but do not draw every semantic item as a box.

Use visible boxes for:

- source-grounded modules;
- operations;
- systems;
- stages;
- regions or lanes;
- justified data/artifact objects that must be seen.

Prefer edge/port labels for:

- variables;
- intermediate outputs;
- scores and metrics;
- weights and parameters;
- masks, states, rewards, constraints, and pass-through artifacts.

### Edge-label-first policy

Before rendering, classify each non-module term:

- `inline_edge_label`
- `port_label`
- `attached_tag`
- `labeled_fork_or_merge`
- `small_artifact_glyph`
- `standalone_module_box`
- `caption_only`
- `removed`

Default to `inline_edge_label`. Allow `standalone_module_box` only when the source shows the term functions as an actual operation or module.

### Internal motif for compound modules

Do not turn important compound modules into empty titled boxes. If a core module hides substeps, give it a compact internal motif:

- mini-chain;
- stacked motifs;
- side cutaway;
- micro-pipeline;
- small gate/filter/merge/select glyphs.

Keep labels short. Use 0 to 4 words inside micro-motifs when possible.

### Visual information economy

Repeated elements must earn space. Compress repetitions unless each visible copy adds meaning.

Use:

- grouped stacks;
- ellipses;
- braces;
- one representative flow plus peer markers;
- one loop arrow with update label;
- a compact legend entry;
- a small comparison chip.

Avoid:

- repeated full workflow rows for equivalent actors;
- repeated labels in the body, legend, and caption;
- decorative icons with no method, system, workflow, or legacy campaign meaning;
- dense grids unless the task is explicitly evidence or distribution focused.

### Caption and legend co-design

For academic diagrams, plan the caption/legend as part of the figure logic. The figure body should carry non-droppable steps; the caption should define symbols, assumptions, scope, and claim boundaries.

For legacy campaign diagrams, use side notes or legend for audience definitions, channel terms, KPI definitions, and non-visual constraints; do not overload the main route with paragraph text.

### Candidate brief fields

When proposing alternatives or preparing a final selected rendering, record:

- candidate ID or option ID;
- figure title;
- figure sentence;
- reader path;
- selected subtype;
- selected layout;
- selected visual style;
- visible text contract;
- edge/port contract;
- density budget;
- repetition compression plan;
- caption/legend support plan;
- missing information risk;
- output formats.

## Route JSON additions

Use these optional fields when the diagram is academic, engineering-facing, or a legacy campaign route:

```json
{
  "audience": "academic",
  "figure_subtype": "academic_method_framework",
  "reader_question": "What is the proposed method and how do its modules interact?",
  "reader_path": ["Problem", "Input", "Core method", "Validation", "Output"],
  "visible_text_contract": {
    "visible_node_labels": [],
    "visible_edge_or_port_labels": [],
    "visible_internal_micro_labels": [],
    "visible_legend_or_caption_labels": [],
    "internal_text_blacklist": ["node_id", "edge_id", "file paths", "audit keys"]
  },
  "density_budget": {
    "top_level_module_budget": 7,
    "density_verdict": "balanced",
    "merge_actions": []
  },
  "caption_support_plan": {
    "figure_body_carries": [],
    "caption_or_legend_carries": [],
    "risk_if_caption_only": []
  }
}
```

## Human-choice boundary

`tech-route-maker` differs from the source project: it produces editable diagram files, not final raster paper figures. Still, keep the human-choice boundary: users select output formats, layout, style, and subtype explicitly before rendering.
