# VAS Benchmark Summary Tables (`SOFTWARE_FIXTURE_ONLY`)

## Table 1: Condition-Level Event Rates, Attack Success Rate (ASR), and False Refusal Rate (FRR)

| Track | Condition (`condition_id`) | Role | Planned | Observed | Events | Event Rate (%) | Key Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| A | `neutral_text` | Text baseline | 24 | 24 | 0 | 0.00% |  |
| A | `claim_text` | Text claim | 24 | 24 | 2 | 8.33% |  |
| A | `neutral_image` | Image baseline | 24 | 24 | 0 | 0.00% | Baseline Unauthorized Rate (Neutral Image) |
| A | `claim_image` | Image claim | 24 | 24 | 3 | 12.50% | Visual Spoofing ASR (Unauthorized Claim Image) |
| A | `none_empty` | No-document control | 24 | 24 | 0 | 0.00% |  |
| A | `claim_image_authorized` | Authorized control | 24 | 24 | 24 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| A | `claim_image_wrong_scope` | Scope control | 24 | 24 | 5 | 20.83% |  |
| A | `none_authorized` | Authorized baseline | 24 | 24 | 24 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |
| B | `neutral_text` | Text baseline | 24 | 24 | 0 | 0.00% |  |
| B | `claim_text` | Text claim | 24 | 24 | 2 | 8.33% |  |
| B | `neutral_image` | Image baseline | 24 | 24 | 0 | 0.00% | Baseline Unauthorized Rate (Neutral Image) |
| B | `claim_image` | Image claim | 24 | 24 | 6 | 25.00% | Visual Spoofing ASR (Unauthorized Claim Image) |
| B | `none_empty` | No-document control | 24 | 24 | 0 | 0.00% |  |
| B | `claim_image_authorized` | Authorized control | 24 | 24 | 24 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| B | `claim_image_wrong_scope` | Scope control | 24 | 24 | 3 | 12.50% |  |
| B | `none_authorized` | Authorized baseline | 24 | 24 | 24 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |

## Table 2: Paired Causal Contrasts (Percentage Points & 95% Cluster Bootstrap CI)

| Track | Contrast | Complete Pairs | Estimate (pp) | 95% Cluster CI (pp) | p_raw | p_Holm |
|---|---|---:|---:|---|---:|---:|
| A | Primary Image Claim (`claim_image - neutral_image`) | 24 | +12.50 | [+8.33, +16.67] | — | — |
| A | Transcript Claim (`claim_text - neutral_text`) | 24 | +8.33 | [+0.00, +16.67] | — | — |
| A | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 24 | +79.17 | [+66.67, +91.67] | — | — |
| B | Primary Image Claim (`claim_image - neutral_image`) | 24 | +25.00 | [+12.50, +37.50] | — | — |
| B | Transcript Claim (`claim_text - neutral_text`) | 24 | +8.33 | [+8.33, +8.33] | — | — |
| B | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 24 | +87.50 | [+79.17, +95.83] | — | — |
