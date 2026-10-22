# B 题（优化决策类）项目配置经验与坑点

本文档记录 contest-orchestrator B 题优化加固工程中发现的所有配置坑点、字段格式和调试经验。其他 agent 在搭建 B 题项目时应先阅读本文档，避免重复踩坑。

## 1. H7 图表相关

### 1.1 图表字段名

**坑点**：figure_registry.yaml 中图表的路径字段名是 `svg` 和 `png`，不是 `svg_path` 和 `png_path`。

**正确格式**：
```yaml
figures:
  - figure_id: q1_result
    kind: data
    generator: modelviz
    svg: figures/q1_result.svg      # 字段名是 svg，不是 svg_path
    png: figures/q1_result.png      # 字段名是 png，不是 png_path
    svg_sha256: "..."
    png_sha256: "..."
```

**检查器逻辑**：`_validate_h7_figures()` 读取 `svg` 和 `png` 字段，检查文件是否存在。如果字段名错误，会报"图表产物缺失"。

### 1.2 图表路由硬约束

每张图必须包含：
- `kind`：data/flowchart/roadmap/schematic/drawio
- `generator`：匹配路由（data→modelviz，flowchart/roadmap→tech-route-maker，schematic→tikz-scientific-figures，drawio→drawio-diagram）
- `formats`：必须含 svg+png
- `insertion_format`：svg
- `visual_qa`：passed/reviewed

不满足即 BLOCK。

## 2. H8 论文素材相关

### 2.1 paper_material_readiness verified_by

**坑点**：`verified_by` 必须为字符串 `"H6"`，不是 `"H6-agent-01"` 或其他格式。

**正确格式**：
```yaml
status: PASS
prepared_by: H8-agent-01
verified_by: "H6"                              # 必须是 "H6"
verification_agent_instance_id: H6-agent-01   # 这里才是实例 ID
```

**检查器逻辑**：`_validate_paper_materials()` 检查 `verified_by == "H6"` 且 `verification_agent_instance_id == nodes["H6"]["agent_instance_id"]`。

### 2.2 sensitivity_or_robustness 字段（P0-03 新增）

B 题（优化决策类）每个子问题必须登记 `sensitivity_or_robustness` 字段：

```yaml
subproblems:
  - id: Q1
    materials:
      problem_mapping: {path: paper/Q1_mapping.md, sha256: "..."}
      # ... 其他 9 个字段
      sensitivity_or_robustness:              # P0-03 新增字段
        path: results/sensitivity_report.yaml
        sha256: "..."
        # 或者：
        # not_applicable: true
        # not_applicable_reason: "该子问题不涉及优化"
```

如果 `not_applicable: true`，必须提供 `not_applicable_reason`。

### 2.3 target_length sections material_refs

**坑点**：`target_length.sections` 中，除了 `narrative_only` 类型的章节，其他类型（包括 `evidence` 和 `appendix`）都必须有 `material_refs` 字段，且是一个非空列表，每个引用都必须是新鲜的（文件存在且哈希匹配）。

**正确格式**：
```yaml
target_length:
  min_pages: 20
  max_pages: 30
  whole_pdf_recommended_range: [35, 51]
  sections:
    - chapter_id: ch1
      title: 问题分析
      page_count: 3
      chapter_type: narrative_only     # narrative_only 不需要 material_refs
      capacity_status: adequate
    - chapter_id: ch2
      title: 模型建立
      page_count: 5
      chapter_type: evidence           # evidence 必须有 material_refs
      capacity_status: adequate
      material_refs:
        - {path: paper/Q1_assumptions.md, sha256: "..."}
        - {path: paper/Q1_symbols.md, sha256: "..."}
    - chapter_id: appendix
      title: 附录
      page_count: 10
      chapter_type: evidence           # appendix 也必须有 material_refs（不要用 appendix 类型）
      capacity_status: adequate
      material_refs:
        - {path: paper/Q1_literature.md, sha256: "..."}
```

**注意**：`chapter_type: appendix` 不会跳过 material_refs 检查，只有 `narrative_only` 会跳过。建议附录章节也使用 `evidence` 类型并提供 material_refs。

### 2.4 whole_pdf_recommended_range

必须为 `[35, 51]`，其他值会报错。

## 3. H9 交付相关

### 3.1 input_manifest.yaml 格式（P0-06 新增）

**坑点**：H9 输入哈希不是对整个 YAML 文件计算哈希，而是按路径排序的 `path:sha256` 列表的 SHA-256。

**正确格式**：
```yaml
schema_version: "1.0"
files:
  - path: paper/paper.pdf
    sha256: "实际文件的 SHA-256"
  - path: paper/paper.tex
    sha256: "实际文件的 SHA-256"
  # ... 其他输入文件
```

**检查器逻辑**：`_validate_h9_delivery()` 读取 `input_manifest.files`，对每个文件计算实际 SHA-256，构建 `path:sha256` 字符串列表，按路径排序，用换行符连接，计算整个字符串的 SHA-256，与 `input_sha256` 字段比对。

### 3.2 H9 必须提供 input_manifest

H9 节点必须登记 `input_manifest` 字段，指向 `results/input_manifest.yaml`。没有 input_manifest 会报"H9 输入哈希自报缺失"。

## 4. evidence_gap_matrix 相关

### 4.1 必须覆盖全部已检测缺口

**坑点**：`evidence_gap_matrix.yaml` 中的 `gaps` 列表必须与 `_collect_material_gaps()` 检测到的缺口完全匹配，包括 `subproblem_id`、`requirement`、`responsible_node` 三个字段。

**正确格式**：
```yaml
schema_version: "1.0"
readiness_sha256: "paper_material_readiness.yaml 的实际 SHA-256"
gaps:
  - gap_id: GAP-001
    subproblem_id: Q1
    requirement: sensitivity_or_robustness
    responsible_node: H6
    required_artifact: results/sensitivity_report.yaml
    acceptance_criteria: "status=verified, 扰动点数值完整"
    return_to: H6
    priority: high
# 如果没有缺口：
# gaps: []
# all_gaps_covered: true
# status: no_gaps
```

**检查器逻辑**：`_validate_gap_matrix()` 计算 `expected = {(gap["subproblem_id"], gap["requirement"], gap["responsible_node"]) for gap in gaps}`，然后与 `actual` 比对，如果不相等就报"未覆盖全部已检测缺口"。

### 4.2 readiness_sha256 必须绑定

`evidence_gap_matrix.readiness_sha256` 必须与 `paper_material_readiness.yaml` 的实际 SHA-256 一致。修改 readiness 后必须更新这个字段。

## 5. user_approval 循环依赖

### 5.1 问题描述

每次修改任何审查包相关文件后，`approval_log.yaml` 中的哈希都会过期，需要重新计算。这是检查器的设计特性，不是 bug。

### 5.2 解决方案

修改审查包后，重新运行以下步骤：
1. 重新计算每个审查包的 SHA-256
2. 更新 `approval_log.yaml` 中的 `artifact_digests`
3. 重新运行 `check_harness_control.py`

### 5.3 实际比赛中的处理

实际比赛中，审查包修改后需要重新获得用户批准。这是正常的工作流程，不需要自动化。

## 6. H6 验证相关

### 6.1 global_interface_check 接口字段（P1-02 新增）

**坑点**：`global_interface_check.yaml` 中每个子问题的 `interface_fields` 必须是结构化对象，包含 `field`、`unit`、`comparison_status`、`source_path`、`source_sha256` 字段，不能是占位符字符串。

**正确格式**：
```yaml
per_subproblem:
  Q1:
    interface_fields:
      - field: decision_variable_x
        unit: "吨"
        comparison_status: consistent
        source_path: results/result.json
        source_sha256: "..."
      - field: objective_value
        unit: "万元"
        comparison_status: consistent
        source_path: results/result.json
        source_sha256: "..."
```

### 6.2 跨问接口字段

H6 节点必须登记 `global_interface_check`，包含以下字段：
- `checks`：对象，包含 9 个布尔字段，全部必须为 True
  - `shared_symbols`
  - `units`
  - `data_versions`
  - `upstream_downstream_fields`
  - `time_scales`
  - `parameters`
  - `cross_question_constraints`
  - `conclusions`
  - `provenance`
- `status`：必须为 "PASS" 或 "PAUSE"
- `issues`：列表，status=PASS 时必须为空
- `verified_by`：必须为 "H6"
- `verification_agent_instance_id`：必须与 H6 节点的 agent_instance_id 一致
- `per_subproblem`：必须是列表（不是 dict），每个条目包含 subproblem_id 和 interface_fields
- `task_card_path` 和 `task_card_sha256`：必须登记 H6 任务卡路径和哈希

缺少 `checks` 字段或某个字段不为 True 会报"跨问接口待修复"。

**正确格式示例**：
```yaml
status: PASS
checks:
  shared_symbols: true
  units: true
  data_versions: true
  upstream_downstream_fields: true
  time_scales: true
  parameters: true
  cross_question_constraints: true
  conclusions: true
  provenance: true
issues: []
verified_by: "H6"
verification_agent_instance_id: H6-agent-01
per_subproblem:
  - subproblem_id: Q1
    interface_fields:
      - field: optimal_x
        unit: "吨"
        comparison_status: consistent
        source_path: results/result.json
        source_sha256: "64位十六进制字符串"
```

## 7. dispatch_records 相关

### 7.1 spawn_receipt 校验（P1-03 新增）

每个 dispatch_record 必须包含 `spawn_receipt`，包含：
- `task_id`
- `agent_instance_id`
- `task_card_sha256`
- `model`
- `reasoning_effort`

`dispatched_at` 必须是 ISO 格式时间戳。
`harness_run_id` 必须绑定。

### 7.2 task_card_sha256

`dispatch_records[].task_card_sha256` 必须与 `.contest/task_cards/H*.yaml` 的实际 SHA-256 一致。修改任务卡后必须更新这个字段。

## 8. H8 写作计划相关

### 8.1 篇幅约束（P1-04 新增）

`writing_plan.yaml` 中每章必须登记：
- `page_count`
- `material_refs`
- `figure_locations`
- `claim_ids`

正文页数硬上限 30 页，推荐下限 20 页。

### 8.2 paper_source（P1-05 新增）

H8 必须登记 `paper_source`（论文源文件路径+SHA-256），每个 `paper_anchor` 必须在论文源文件中实际存在。

### 8.3 paper_claim_coverage 详细格式

`paper_claim_coverage.yaml` 是 H8 节点的主张覆盖表，格式要求非常严格：

**顶层字段**：
- `status`：必须为 "PASS"
- `readiness_sha256`：必须与 `paper_material_readiness.yaml` 的实际 SHA-256 一致
- `paper_source`：论文源文件路径和 SHA-256
- `claims`：列表，必须与 `paper_material_readiness.yaml` 中的 `claim_requirements` 完全匹配（ID 集合一致）

**claims 条目格式**：
- `id`：必须使用 `id` 字段（不是 `claim_id`），必须与 claim_requirements 中的 id 一致
- `type`：只能是以下四种之一
  - `citation_use`：需要 `literature_use` 字段
  - `conclusion`：需要 `quantified_results` 和 `validation` 两个字段
  - `figure_claim`：需要 `figures_or_tables` 和 `quantified_results` 两个字段
  - `quantified_result`：需要 `quantified_results` 字段
- `paper_anchor`：必须在论文源文件中实际存在（建议使用章节标题）
- `evidence_refs`：必须是一个非空列表，每个引用必须是新鲜的（文件存在且哈希匹配），且必须在 `paper_material_readiness.yaml` 的 `material_refs` 中登记

**常见错误**：
1. 使用 `claim_id` 而不是 `id` → 报"论文主张覆盖表必须覆盖且只能覆盖准入主张"
2. 使用不允许的主张类型（如 `result`、`sensitivity`）→ 报"使用未知主张类型"
3. evidence_refs 引用的文件不在 material_refs 中 → 报"使用未冻结或过期证据"
4. 主张类型需要的字段不完整 → 报"证据类型不完整"
5. paper_anchor 不在论文源文件中 → 报"paper_anchor 未在论文源文件中出现"

**正确格式示例**：
```yaml
status: PASS
readiness_sha256: "paper_material_readiness.yaml 的实际 SHA-256"
paper_source:
  path: paper/paper.tex
  sha256: "paper.tex 的实际 SHA-256"
claims:
  - id: C-001
    type: quantified_result
    paper_anchor: "求解结果"
    evidence_refs:
      - path: paper/Q1_results.md
        sha256: "Q1_results.md 的实际 SHA-256"
  - id: C-002
    type: conclusion
    paper_anchor: "结论"
    evidence_refs:
      - path: paper/Q1_results.md
        sha256: "..."
      - path: paper/Q1_validation.md
        sha256: "..."
```

## 9. 灵敏度报告相关

### 9.1 三重硬约束（P0-02 新增）

`check_model_evidence.py` 的 `_check_sensitivity_report()` 增加三重硬约束：
1. `status` 只允许 `verified`（不允许 `pending`、`draft` 等）
2. `subproblem_id` 必须绑定到具体子问题
3. 扰动点数值完整性（每个扰动点必须有 `parameter`、`baseline_value`、`perturbed_value`、`objective_change`）

### 9.2 报告位置

灵敏度报告可以放在以下位置：
- 项目根目录：`sensitivity_report.yaml` 或 `robustness_report.yaml`
- `results/` 目录
- `04_结果/` 目录
- `validation/` 目录
- `05_验证/` 目录

检查器会自动搜索这些位置。

## 10. 状态转移历史（P1-01 新增）

`.contest/status_history.yaml` 必须记录每个节点的状态变更，按时间顺序逐条校验状态转移合法性和连续性。

状态转移合法路径：
- `not_started` → `draft` → `review_pending` → `approved` → `frozen`
- 任何状态 → `evidence_gap` → `draft`
- `approved` → `stale` → `draft`

## 11. 摘要合同（P0-04 新增）

`check_abstract_contract.py` 增加 `--capabilities` 参数，用于检查摘要是否覆盖了 problem_profile.yaml 中声明的所有能力。

用法：
```bash
python scripts/check_abstract_contract.py <论文目录> --project-root <项目目录> --capabilities
```

## 12. 调试技巧

### 12.1 查看检查器源码

所有硬约束的真正权威来源是 `scripts/check_harness_control.py`，不是 SKILL.md。遇到不明报错时，直接在源码中搜索错误消息。

### 12.2 逐步排查

如果检查失败，按以下顺序排查：
1. 读取检查结果 JSON，查看具体的 failures 和 missing
2. 在 `check_harness_control.py` 中搜索错误消息，找到校验逻辑
3. 对照校验逻辑，检查配置文件的字段名和格式
4. 修改配置文件后重新运行检查

### 12.3 哈希计算

所有 SHA-256 哈希都是对文件内容计算的，不是对文件路径或其他元数据。修改文件内容后必须重新计算哈希。

Windows 下计算哈希：
```powershell
Get-FileHash -Algorithm SHA256 <文件路径>
```

Python 下计算哈希：
```python
import hashlib
hashlib.sha256(Path(file).read_bytes()).hexdigest()
```

---

**最后更新**：2026-09-06
**维护者**：contest-orchestrator B 题优化加固工程
