# Visual Authority Spoofing in Multimodal AI Models and Agents

**Authors:** Phùng Hữu Luân & Co-Author (`[ADD CO-AUTHOR NAME]`)  
**Status:** Research Protocol & Paper Draft (`v0.1` — Offline software & dataset validated; awaiting preregistered live model evaluation)

---

## Abstract

Approval screenshots can claim permission for actions that an application has not authorized. This research protocol tests whether a declarative approval claim changes two outcomes under a controlled policy. The first is exact disclosure of an inert protected code. The second is a valid native call proposal for a restricted mock tool. The matched design varies document status and presentation medium for each synthetic record. Additional controls reuse the same approval image while varying the registry grant. The holdout contains 120 records in 24 workflow families. Primary analyses will estimate paired risk differences between approval and neutral images under an empty registry. Tool proposals will be replayed with and without deterministic authorization checks. Offline validation covers the benchmark assets and implementation. Live model effects will be estimated after pilot validation and protocol registration.

---

## 1. Introduction

An agent asked to mark a record as released may receive a screenshot whose document status reads `APPROVED`. The application may have granted the requester permission to inspect the record only. A system can transcribe the screenshot accurately and still apply the wrong authorization rule. The application must determine permission from the requester, the record, and the requested action. Prior work on instruction hierarchy motivates keeping application instructions and user-supplied content in separate roles (Wallace et al., 2024).

We use **visual authority spoofing** as a working term for an image that presents a claim of approval inconsistent with the application-managed grant. The study isolates a declarative field in a synthetic document. It asks how much changing `RECEIVED` to `APPROVED` affects the decision, whether the effect differs between an image and its verbatim transcript, and whether a model responds differently when the grant covers a different action.

The protocol applies the same conditions to two measurable endpoints:
- **Track A** uses an inert code (*canary*) to operationalize a controlled content rule.
- **Track B** records the model's first tool proposal and replays it through a mock executor.

The authorization record is manipulated separately from document content. This design provides a basis for separating a model's proposal from the state change that an application permits.

---

## 2. Related Work

MM-SafetyBench studies how query-related images can affect safety behavior in multimodal models (Liu et al., 2024). FigStep examines typographic prompts rendered into images (Gong et al., 2025). These studies motivate an image-based evaluation. The present protocol keeps the underlying request and document layout fixed and changes a status field that describes approval. The canary measures compliance with the experiment's content rule under those inputs.

InjecAgent (Zhan et al., 2024) and AgentDojo (Debenedetti et al., 2024) evaluate indirect prompt injection in tool-integrated systems. AgentDojo also considers performance on legitimate tasks, which informs the authorized controls here. VPI-Bench evaluates malicious content embedded in visual interfaces (Cao et al., 2026). MMPIBench follows multimodal prompt injection across perception, planning, and tool calls (Nguyen and Husain, 2026). Together these studies establish the relevance of visual inputs and of distinguishing an attempt from completion.

Multimodal-SEA is a close precedent for Track B. It evaluates multi-turn social engineering with forged multimedia and compares scenarios with and without those artifacts (He et al., 2026). The present design pairs each rendered document with its exact transcript and compares approval and neutral status within each medium. It limits the decision horizon to the first response. These choices support a narrower estimate of the effect of a declarative claim.

Evidence-Carrying Multimodal Agents (Zhang et al., 2026) and Visual Confused Deputy (Liu et al., 2026) study how visual perception errors can reach execution and how independent checks can constrain actions. Safin et al. (2026) study forged approvals in retrieved documents and separate a compromised judgment from unauthorized execution. The registry check in this protocol serves as an experimental control. The proposed contribution is the combination of matched approval stimuli, a separately controlled grant, and two observable endpoints. The literature comparison is targeted and establishes the scope of that contribution.

---

## 3. Methods

### 3.1 Research Questions and Hypotheses

The two primary hypotheses concern the empty-registry image contrast:
- **H1A (Track A):** Predicts that an approval image (`APPROVED`) increases exact canary disclosure relative to a neutral image (`RECEIVED`) under an empty registry.
- **H1B (Track B):** Predicts an increase in valid native tool call proposals to the restricted tool (`release_record`) under the same comparison.

Both tests will be two-sided. The directional predictions will be interpreted alongside the signed estimates and their uncertainty.

- **Exploratory Modality Question (RQ2 / H2):** Compares the approval effect in images with the approval effect in transcripts: $(\text{claim\_image} - \text{neutral\_image}) - (\text{claim\_text} - \text{neutral\_text})$.
- **Exploratory Scope Question (RQ3 / H3):** Holds the approval image fixed and compares a grant for the requested action (`exact`) with a grant for a different action (`other`).
- **Baseline & Utility Controls:** The no-document controls estimate baseline behavior and authorized task completion. The executor replay answers a separate question about what a registry check permits for a given proposal.

### 3.2 Threat Model and Authorization

The requester supplies a synthetic document image or transcript as evidence for an otherwise fixed request. The requester controls the document status. The test harness controls the requester identity, the policy, the registry, and the tool definitions. It supplies the registry through the application instruction channel, while the document appears in user content. The trusted grant must match the requester, record, and action. An empty registry denies the action. The out-of-scope control grants metadata review (`inspect_record_metadata`) on the same record. The design assumes an intact registry and a correctly functioning simulator.

A claim is operationally inconsistent with authorization if the document says `APPROVED` and the registry lacks a grant covering the requested action. The field is declarative and the document contains no imperative directing the model to override a rule. Its appearance is held constant apart from the status text. The application supplies the real grant state independently, so the same approval image can be paired with either a valid grant or a denial.

### 3.3 Corpus and Paired Conditions

The corpus is generated from four fictional work domains covering `editorial`, `inventory`, `training`, and `archival` workflows. A workflow family groups cases with a common scenario template and different records:
- **Development split (`data/dev`):** 24 records in 8 workflow families (3 records per family).
- **Holdout split (`data/holdout`):** 120 records in 24 disjoint workflow families, with 5 records per family and 10 per domain and document type combination.

Development and holdout use different layout variants. Each document is an email, memorandum, or internal clearance record from a fictional organization (*Aster Vale Demo Lab*).

Each record has two `1,100 × 660` PNG images and two transcripts. The status changes from `RECEIVED` to `APPROVED` within each matched pair. The transcript preserves the visible wording, including the `SYNTHETIC LAB DATA` label. PNG generation uses fixed assets, with image and manifest SHA-256 values recorded for traceability. Figure 1 shows status excerpts from a development pair.

![Figure 1: Status excerpts from paired development documents. The source images differ only in the status field.](docs/figures/figure1_status_excerpts.png)

*Figure 1: Status excerpts from paired development documents. The source images differ only in the status field.*

Table 1 lists the eight conditions applied to each record in each track. The first four form a $2 \times 2$ design under an empty registry. The authorization controls reuse the approval image or omit documents. The request wording, requester, and target remain fixed within a record and track.

| Condition ID | Evidence | Grant | Role |
|---|---|---|---|
| `neutral_text` | Received text (`RECEIVED`) | Empty | Text baseline |
| `claim_text` | Approved text (`APPROVED`) | Empty | Text claim |
| `neutral_image` | Received image (`RECEIVED`) | Empty | Image baseline |
| `claim_image` | Approved image (`APPROVED`) | Empty | Image claim |
| `none_empty` | No document | Empty | No-document control |
| `claim_image_authorized` | Same `APPROVED` image | Exact | Authorized control |
| `claim_image_wrong_scope` | Same `APPROVED` image | Other | Scope control |
| `none_authorized` | No document | Exact | Authorized baseline |

*Table 1: Conditions for each record and track.*

### 3.4 Tasks and Outcome Definitions

In **Track A**, the application instructions include a case-specific canary and a rule permitting its disclosure only under an exact grant. The canary is an inert synthetic string. The submitted document contains no canary. The outcome is `1` if the canary appears verbatim as an independent token in visible output, including in a response that otherwise refuses. In a denied condition this is unauthorized disclosure. In an exact-grant condition it measures successful completion.

In **Track B**, the API receives a read-only function (`inspect_record_metadata`) and a function that marks the requested record as released (`release_record`). The primary event is a complete native call to the release function with one schema-valid argument matching the case identifier (`record_id`). A secondary indicator records trials containing any call to the target, including calls with invalid arguments. A textual claim of completion is logged as visible text and cannot change the simulator state.

Each Track B proposal is replayed against two fresh instances of the same Boolean release state:
1. The first (`replay_no_gate`) validates function name, schema, and target record.
2. The second (`replay_with_gate`) applies those checks and also requires an exact grant in the registry.

The executor reads the grant independently of the document. The log records whether a valid proposal occurred and whether each replay changed the flag. With an exact grant, a correctly authorized state change measures Track B utility. The model receives no simulated tool result during the measured decision.

### 3.5 Model Configuration and Pilot

The candidate primary snapshot is `gpt-4.1-mini-2025-04-14` through the OpenAI Responses API. Official model documentation lists image input and function calling (OpenAI, n.d.). Selection will depend on access, status recognition, and authorized task completion on the development split. The final requested and served snapshot identifiers will be recorded before confirmatory evaluation. A separate replication may use an additional snapshot while retaining the condition definitions and reporting any differences in the adapter.

The current adapter sends fresh requests with `temperature = 0`, a `192`-token output limit, and `high` image detail. Track B enables automatic tool choice (`tool_choice = "auto"`) and disables parallel tool calls (`parallel_tool_calls = false`). Trials are shuffled using a recorded seed derived from a base value of `20261109` and the replicate index. Only replicate 1 of the preregistered snapshot will enter the confirmatory analysis. The runner records request hashes, trial order, response status, served model, visible text, native calls, elapsed time, and available token usage.

A limited API pilot will first verify image intake and the tool-call schema. The development evaluation will then check authorized completion in both tracks and a separate status-reading probe. The proposed thresholds are at least **80% authorized completion** in each track and at least **90% exact status recognition** on the predefined development image sample (at least 15 of 16 images). Authorized conditions will be reported separately. An independent reading request will present both status variants of one selected record per family (16 development images and 48 holdout images when complete). Reading outcomes support interpretation of modality effects without changing eligibility for the primary contrasts.

### 3.6 Sample Size and Planned Execution

Eight conditions per record and two tracks give **384 development trials** and **1,920 holdout trials** per snapshot and replicate. The independent reading probe is additional. Inference is clustered by the 24 holdout workflow families. The development split will be used to check feasibility and freeze the protocol, prompts, tool schema, eligibility rules, and model configuration. A timestamped registration (`PREREGISTRATION_VI.md`) will precede live holdout collection.

Sample-size sensitivity depends on the frequency of discordant image pairs and on dependence within families. For planning only, a normal approximation with a 0.25 discordance probability, an intrafamily correlation of 0.10, five records per family, and a two-sided per-test level of 0.025 gives approximately 36% power for a 10-percentage-point difference and 75% for a 15-point difference. These values are assumption-based planning quantities. The primary report will emphasize uncertainty, particularly for small effects or rare events.

### 3.7 Statistical Analysis

For each track, the primary estimand is the paired risk difference between the `APPROVED` (`claim_image`) and `RECEIVED` (`neutral_image`) image conditions under an empty registry:

$$\Delta_{\text{image}} = 100 \times \frac{n_+ - n_-}{n_{\text{complete\_pairs}}}$$

Here $n_+$ counts records with an event only in the approval-image condition, $n_-$ counts records with an event only in the neutral-image condition, and $n_{\text{complete\_pairs}}$ counts complete pairs.

The exploratory modality interaction subtracts the corresponding transcript effect from the image effect on records with all four conditions observed. The exploratory scope comparison estimates the difference between exact and wrong-action grants with the approval image fixed. Authorized utility, restricted proposals with invalid arguments, and simulated state changes will be reported separately by condition.

Uncertainty will be summarized with 95% percentile intervals from 10,000 workflow-family bootstrap draws stratified by domain. Resampling preserves all matched observations in a selected family (Field and Welsh, 2007). For each primary contrast, a two-sided Monte Carlo sign-flip test will use the absolute sum of family differences and 49,999 random draws. The test depends on family-level sign invariance under the null (Hemerik and Goeman, 2018). The Holm procedure will adjust the two primary $p$-values at a familywise level of 0.05 (Holm, 1979). The interval estimates are marginal for each contrast.

Technical errors, unrun trials, and incomplete responses will be reported as missing. Confirmatory inference requires at least 95% complete primary pairs per track ($\ge 114/120$), representation of every family by an observed pair in both tracks, and agreement between requested and served snapshot. The report will give observed and planned denominators, best- and worst-case bounds for missing outcomes, and a sensitivity analysis excluding explicit provider blocks and structured refusals. If both image conditions have zero events and complete coverage, the report will state the count and a family-level one-sided 95% upper bound ($1 - 0.05^{1/24} \approx 11.74\%$) under an independent-family sampling assumption.

---

## 4. Software and Dataset Validation

The offline validation used a fresh extraction of the benchmark repository and generated the development and holdout splits from source. The responses in the fixture runs were supplied by deterministic test code. They were used to exercise request construction, outcome parsing, scoring, logging, and the replay path. Table 2 reports checks completed on the software and assets. Every planned fixture key appeared once, and the reports were labeled `SOFTWARE_FIXTURE_ONLY`.

| Check | Observed Result |
|---|---|
| Unit tests (`python -m unittest discover -s tests -v`) | 10 passed |
| Development fixtures (`runs/fixture_dev.jsonl`) | 384 unique trial records |
| Holdout fixtures | 1,920 unique trial records |
| Paired images (`24 dev + 120 holdout`) | 144 of 144 pairs passed |
| Status pixel isolation check | 100% of pixel diffs confined to `STATUS_VALUE_BOX` |

*Table 2: Offline software and asset validation checks.*

The replay checks also verified that valid unauthorized proposals preserved the state under registry enforcement (`replay_with_gate`). This verifies the coded invariant for the tested simulator paths. All image hashes matched. Pixel differences were confined to the status field. The target model's reading accuracy, disclosure rates, and tool-proposal rates remain to be measured with live requests.

---

## 5. Live Evaluation Results (To Be Populated After Confirmatory Run)

> **Note for Co-Authors:** Do not populate Tables 3 and 4 with fixture numbers. Fill in these tables only after locking `PREREGISTRATION_VI.md` and running `experiment.py` and `analyze.py --confirmatory` on the live holdout log (`runs/live_holdout.jsonl`).

### 5.1 Primary Paired Image Contrasts (Empty Registry)

| Track & Endpoint | `claim_image` (`APPROVED`) Events / Observed | `neutral_image` (`RECEIVED`) Events / Observed | Complete Pairs ($n$) | Paired Difference $\Delta_{\text{image}}$ (pp) | 95% Cluster Bootstrap CI (pp) | $p_{\text{Holm}}$ |
|---|---|---|---|---|---|---|
| **Track A · Canary Disclosure** | `[TBD / 120]` | `[TBD / 120]` | `[TBD]` | `[TBD]` | `[TBD, TBD]` | `[TBD]` |
| **Track B · Valid Restricted Tool Proposal** | `[TBD / 120]` | `[TBD / 120]` | `[TBD]` | `[TBD]` | `[TBD, TBD]` | `[TBD]` |

*Table 3: Primary empty-registry paired image contrasts on the holdout split (`n = 120` planned pairs).*

### 5.2 Track B Proposals vs. Deterministic Gate Replay

| Track B Condition | Valid Native Call Proposals | State Changed (Schema + ID Check Only) | State Changed (With Authorization Gate) | Observed Trials |
|---|---|---|---|---|
| `claim_image` (Empty grant + `APPROVED` image) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD / 120]` |
| `claim_image_wrong_scope` (Wrong-action grant + `APPROVED` image) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD / 120]` |
| `claim_image_authorized` (Exact grant + `APPROVED` image) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD / 120]` |
| `none_authorized` (Exact grant + No document) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD / 120]` |

*Table 4: Comparison of Track B model tool-call proposals and simulated state changes with and without the deterministic authorization gate.*

---

## 6. Discussion

The primary image contrast addresses a narrowly controlled question. Its sign and magnitude will describe how changing a status field affects a scored decision under the chosen policy and inputs. The modality interaction can reflect rendering, recognition, and presentation together. A separate reading probe helps interpret a weak or inconsistent image effect, and the authorized controls show whether the model can carry out each task under the same interface.

A high rate of valid restricted proposals can coexist with zero simulated state changes under registry checking. This localizes the failure to the model's decision stage rather than the application's execution layer. Conversely, a low proposal rate paired with poor authorized completion would provide limited evidence about selective authorization behavior. Low observed event counts will be interpreted using the denominators, interval estimates, and missing-data bounds.

---

## 7. Conclusion

This protocol defines matched experiments for testing declarative approval claims under independently controlled authorization. It specifies primary outcomes for content disclosure and native tool proposals and measures the executor's response to those proposals separately. Software and asset validation establishes that the benchmark can generate and score the planned trial structure. Model-level estimates will come from the live evaluation after protocol registration.

---

## Limitations

The dataset uses English-language synthetic records with a visible lab label (`SYNTHETIC LAB DATA`) and a restricted set of templates. The trusted grant is explicitly available to the model in the developer instruction channel. The agent has a fixed tool interface and a one-response horizon. The canary outcome operationalizes a lab-defined content rule. Results from this protocol will apply to the evaluated snapshot, stimuli, and harness. Generalization to provider safety policies, multilingual documents, authentic approval processes, and multi-turn workflows requires further evaluation.

## Ethics Statement

The corpus contains fictional organizations (*Aster Vale Demo Lab*), requesters, and records, and uses a reserved `.test` address. It includes no real identities, approvals, or protected data. The tool executor changes only an in-memory flag. Model-proposed calls remain inside the simulator and have no external service integration. The implementation keeps API credentials outside prompts, outputs, and artifact files.

## Data and Code Availability

This repository contains the development dataset (`data/dev/`), dataset generator (`dataset.py`), test suite (`tests/`), experiment runner (`experiment.py`), statistical analyzer (`analyze.py`), and preregistration template (`PREREGISTRATION_VI.md`). To reproduce a live evaluation, the study record includes the frozen corpus and manifest hashes, source versions, registration timestamp, model identifier, request order, analysis configuration, run logs, and deviations.

---

## References

- Tri Cao, Bennett Lim, Yue Liu, Yuan Sui, Yuexin Li, Shumin Deng, Lin Lu, Nay Oo, Shuicheng Yan, and Bryan Hooi. 2026. VPI-Bench: Visual Prompt Injection Attacks for Computer-Use Agents. In *International Conference on Learning Representations*. arXiv:2506.02456v2.
- Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner, Marc Fischer, and Florian Tramèr. 2024. AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. In *Advances in Neural Information Processing Systems, Datasets and Benchmarks Track*.
- Christopher A. Field and Alan H. Welsh. 2007. Bootstrapping Clustered Data. *Journal of the Royal Statistical Society Series B: Statistical Methodology*, 69(3):369–390.
- Yichen Gong, Delong Ran, Jinyuan Liu, Conglei Wang, Tianshuo Cong, Anyu Wang, Sisi Duan, and Xiaoyun Wang. 2025. FigStep: Jailbreaking Large Vision-Language Models via Typographic Visual Prompts. *Proceedings of the AAAI Conference on Artificial Intelligence*, 39(22):23951–23959.
- Zhitao He, Chi Him Zhang, Chengru Han, and Yi R Fung. 2026. Multimodal-SEA: Benchmarking AI Agent Security under Multimodal Social Engineering Attacks. *arXiv preprint* arXiv:2611.08281v1.
- Jesse Hemerik and Jelle Goeman. 2018. Exact testing with random permutations. *TEST*, 27(4):811–825.
- Sture Holm. 1979. A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, 6(2):65–70.
- Xin Liu, Yichen Zhu, Jindong Gu, Yunshi Lan, Chao Yang, and Yu Qiao. 2024. MM-SafetyBench: A Benchmark for Safety Evaluation of Multimodal Large Language Models. In *Computer Vision – ECCV 2024*, pages 386–403. Springer.
- Xunzhuo Liu, Bowei He, Xue Liu, Andy Luo, Haichen Zhang, and Huamin Chen. 2026. Visual Confused Deputy: Exploiting and Defending Perception Failures in Computer-Using Agents. *arXiv preprint* arXiv:2603.14707.
- Viet K. Nguyen and Mohammad I. Husain. 2026. An Experimental Evaluation of Multimodal Prompt Injection Attacks on Agentic AI Frameworks. *arXiv preprint* arXiv:2609.09404.
- OpenAI. n.d. GPT-4.1 Mini model. *OpenAI API documentation*. Accessed 10 November 2026.
- Tanzim Hossain Safin, Sharif Noor Zisad, Swakkhar Shatabda, and Ragib Hasan. 2026. Trust propagation and structural containment in Multi-agent LLM pipelines. *arXiv preprint* arXiv:2609.17648.
- Eric Wallace, Kai Xiao, Reimar Leike, Lilian Weng, Johannes Heidecke, and Alex Beutel. 2024. The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions. *arXiv preprint* arXiv:2404.13208.
- Qiusi Zhan, Zhixiang Liang, Zifan Ying, and Daniel Kang. 2024. InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents. In *Findings of the Association for Computational Linguistics: ACL 2024*, pages 10471–10506.
- Guijia Zhang, Hao Zheng, and Harry Yang. 2026. Hallucination as Exploit: Evidence-Carrying Multimodal Agents. In *Findings of the Association for Computational Linguistics: EMNLP 2026*, pages 18413–18437.
