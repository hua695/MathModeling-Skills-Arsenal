# Domain Profiles

Use this reference when the user has not clearly specified the discipline, when the source material belongs to an unfamiliar field, or when the route would be inaccurate without field-specific context.

## Required Domain Context

Every final `tech-route.json` should include:

- `discipline`: broad field, such as computer science, materials science, energy engineering, biomedical science, mechanical engineering, environmental science, agriculture, or social science.
- `subfield`: narrower direction, such as computer vision defect detection, photovoltaic coating materials, integrated energy systems, tumor mechanism research, or survey-based management research.
- `project_type`: paper method figure, thesis proposal, grant application, engineering report, system architecture, experimental workflow, review framework, or course design.
- `research_object`: the concrete object being studied, such as PV modules, coating surface, model architecture, patient samples, robot platform, watershed, or policy mechanism.
- `method_family`: the main method type, such as deep learning, material preparation and characterization, optimization modelling, controlled experiment, statistical modelling, simulation, field survey, or mechanism validation.
- `application_area`: where the result is intended to work.
- `data_or_materials`: source data, samples, materials, devices, documents, or field records.
- `technical_objects`: core modules, variables, devices, algorithms, experiments, interventions, or mechanisms.
- `domain_constraints`: conditions that shape the route, such as sample size, equipment, standards, deployment environment, cost, safety, timeline, or data quality.
- `evaluation_metrics`: how success is measured.
- `expected_outputs`: papers, models, prototypes, datasets, reports, mechanisms, standards, plans, or application deliverables.

If any required domain context is missing, ask one concise clarification question before rendering a final figure.

## Domain Profile Patterns

### Computer Vision / AI

Ask for task type: classification, detection, segmentation, localization, generation, retrieval, prediction, or multimodal fusion.

Route grammar:

`data source -> annotation/preprocessing -> augmentation/balancing -> model architecture -> training -> ablation/comparison -> evaluation -> deployment or application`

Common fields:

- `data_modalities`: RGB, infrared, thermal, EL, hyperspectral, text, audio, sensor, tabular, graph.
- `model_family`: YOLO, CNN, Transformer, U-Net, ResNet, GNN, CLIP, diffusion, autoencoder.
- `metrics`: accuracy, precision, recall, F1, mAP, IoU, AUC, FPS, Params, FLOPs, latency.
- `constraints`: small samples, class imbalance, small targets, real-time inference, edge deployment, domain shift.

Do not mix dataset processing, model modules, and experiment validation into one stage.

### Materials Science

Route grammar:

`material design -> preparation process -> structure/chemistry characterization -> performance testing -> mechanism analysis -> application validation`

Common fields:

- `data_or_materials`: matrix material, additive, coating, substrate, precursor, sample batch.
- `technical_objects`: synthesis route, micro/nano structure, surface chemistry, morphology, interface, durability.
- `metrics`: contact angle, sliding angle, transmittance, adhesion, abrasion resistance, UV stability, efficiency retention.
- `constraints`: process scalability, equipment, environmental exposure, compatibility, repeatability.

Separate preparation, characterization, performance, and mechanism nodes.

### Energy / Engineering Systems

Route grammar:

`system boundary -> source/load/resource data -> model or configuration -> control/operation strategy -> scenario validation -> engineering deliverables`

Common fields:

- `data_or_materials`: load profile, weather, tariff, equipment data, sensor data, site constraints.
- `technical_objects`: PV, storage, grid, thermal load, inverter, controller, optimization model, dispatch rule.
- `metrics`: cost, carbon, reliability, renewable utilization, peak shaving, efficiency, payback, safety.
- `constraints`: standards, budget, grid code, equipment capacity, weather uncertainty, deployment schedule.

Do not force engineering routes into thesis-proposal layouts.

### Biomedical / Life Science

Route grammar:

`research question -> sample/cohort/model -> grouping/intervention -> assay/detection -> mechanism/statistics -> validation -> clinical or biological significance`

Common fields:

- `data_or_materials`: tissue, cells, animals, patients, omics data, imaging, clinical records.
- `technical_objects`: biomarkers, pathways, interventions, assays, phenotypes, controls.
- `metrics`: expression level, survival, sensitivity/specificity, p-value, effect size, phenotype score.
- `constraints`: ethics, sample size, inclusion criteria, batch effects, reproducibility.

Keep sample source, experimental method, mechanism claim, and statistical validation separate.

### Mechanical / Control / Robotics

Route grammar:

`requirement -> system modelling -> mechanism or structure design -> control strategy -> simulation -> prototype/test bench -> performance validation`

Common fields:

- `data_or_materials`: CAD model, sensor data, actuator parameters, load cases, environment.
- `technical_objects`: mechanism, controller, sensor, actuator, simulation model, test bench.
- `metrics`: accuracy, stability, response time, energy consumption, robustness, safety margin.
- `constraints`: manufacturability, control frequency, hardware limits, safety, cost.

### Environmental / Agriculture / Field Science

Route grammar:

`study area/object -> sample or monitoring design -> indicator system -> model/statistics -> spatial/temporal analysis -> validation -> management recommendation`

Common fields:

- `data_or_materials`: field samples, remote sensing data, climate data, soil/water records, survey data.
- `technical_objects`: indicators, model factors, spatial units, treatments, scenarios.
- `metrics`: accuracy, RMSE, biodiversity index, yield, pollution load, risk score.
- `constraints`: sampling season, spatial resolution, missing data, uncertainty, field accessibility.

### Social Science / Management

Route grammar:

`theory foundation -> research hypotheses -> variable design -> data collection -> model construction -> empirical test -> robustness/heterogeneity -> policy or management implications`

Common fields:

- `data_or_materials`: questionnaire, interview, panel data, policy texts, enterprise records.
- `technical_objects`: constructs, variables, mechanisms, mediators, moderators, models.
- `metrics`: reliability, validity, coefficient, significance, fit index, robustness result.
- `constraints`: sample representativeness, endogeneity, measurement validity, policy context.

Do not describe social-science routes as if they were lab workflows.

## Clarification Question Template

When the field is missing, ask:

`To make the technical route accurate, please specify the discipline/subfield, project type, research object, main method family, and success metrics. For example: "computer vision / PV defect detection / paper method figure / YOLO detection / mAP and FPS" or "materials science / self-cleaning coating / thesis proposal / preparation-characterization-testing / contact angle and transmittance."`

