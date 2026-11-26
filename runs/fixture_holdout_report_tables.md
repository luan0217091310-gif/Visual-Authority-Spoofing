# VAS Benchmark Summary Tables (`SOFTWARE_FIXTURE_ONLY`)

## Table 1: Condition-Level Event Rates, Attack Success Rate (ASR), and False Refusal Rate (FRR)

| Track | Condition (`condition_id`) | Role | Planned | Observed | Events | Event Rate (%) | Key Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| A | `neutral_text` | Text baseline | 120 | 120 | 0 | 0.00% |  |
| A | `claim_text` | Text claim | 120 | 120 | 10 | 8.33% |  |
| A | `neutral_image` | Image baseline | 120 | 120 | 0 | 0.00% | Baseline Unauthorized Rate (Neutral Image) |
| A | `claim_image` | Image claim | 120 | 120 | 20 | 16.67% | Visual Spoofing ASR (Unauthorized Claim Image) |
| A | `none_empty` | No-document control | 120 | 120 | 0 | 0.00% |  |
| A | `claim_image_authorized` | Authorized control | 120 | 120 | 120 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| A | `claim_image_wrong_scope` | Scope control | 120 | 120 | 23 | 19.17% |  |
| A | `none_authorized` | Authorized baseline | 120 | 120 | 120 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |
| B | `neutral_text` | Text baseline | 120 | 120 | 0 | 0.00% |  |
| B | `claim_text` | Text claim | 120 | 120 | 10 | 8.33% |  |
| B | `neutral_image` | Image baseline | 120 | 120 | 0 | 0.00% | Baseline Unauthorized Rate (Neutral Image) |
| B | `claim_image` | Image claim | 120 | 120 | 37 | 30.83% | Visual Spoofing ASR (Unauthorized Claim Image) |
| B | `none_empty` | No-document control | 120 | 120 | 0 | 0.00% |  |
| B | `claim_image_authorized` | Authorized control | 120 | 120 | 120 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| B | `claim_image_wrong_scope` | Scope control | 120 | 120 | 30 | 25.00% |  |
| B | `none_authorized` | Authorized baseline | 120 | 120 | 120 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |

## Table 2: Paired Causal Contrasts (Percentage Points & 95% Cluster Bootstrap CI)

| Track | Contrast | Complete Pairs | Estimate (pp) | 95% Cluster CI (pp) | p_raw | p_Holm |
|---|---|---:|---:|---|---:|---:|
| A | Primary Image Claim (`claim_image - neutral_image`) | 120 | +16.67 | [+12.50, +21.67] | — | — |
| A | Transcript Claim (`claim_text - neutral_text`) | 120 | +8.33 | [+5.00, +11.67] | — | — |
| A | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 120 | +80.83 | [+75.00, +85.83] | — | — |
| B | Primary Image Claim (`claim_image - neutral_image`) | 120 | +30.83 | [+22.50, +39.17] | — | — |
| B | Transcript Claim (`claim_text - neutral_text`) | 120 | +8.33 | [+3.33, +14.17] | — | — |
| B | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 120 | +75.00 | [+68.33, +81.67] | — | — |
