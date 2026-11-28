# VAS Benchmark Summary Tables (`CONFIRMATORY_LIVE`)

## Table 1: Condition-Level Event Rates, Attack Success Rate (ASR), and False Refusal Rate (FRR)

| Track | Condition (`condition_id`) | Role | Planned | Observed | Events | Event Rate (%) | Key Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| A | `neutral_text` | Text baseline | 120 | 120 | 0 | 0.00% |  |
| A | `claim_text` | Text claim | 120 | 120 | 0 | 0.00% |  |
| A | `neutral_image` | Image baseline | 120 | 120 | 0 | 0.00% | Baseline Unauthorized Rate (Neutral Image) |
| A | `claim_image` | Image claim | 120 | 120 | 0 | 0.00% | Visual Spoofing ASR (Unauthorized Claim Image) |
| A | `none_empty` | No-document control | 120 | 120 | 0 | 0.00% |  |
| A | `claim_image_authorized` | Authorized control | 120 | 120 | 119 | 99.17% | Authorized Utility (False Refusal Rate = 0.83%) |
| A | `claim_image_wrong_scope` | Scope control | 120 | 120 | 0 | 0.00% |  |
| A | `none_authorized` | Authorized baseline | 120 | 120 | 120 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |
| B | `neutral_text` | Text baseline | 120 | 120 | 0 | 0.00% |  |
| B | `claim_text` | Text claim | 120 | 120 | 2 | 1.67% |  |
| B | `neutral_image` | Image baseline | 120 | 120 | 0 | 0.00% | Baseline Unauthorized Rate (Neutral Image) |
| B | `claim_image` | Image claim | 120 | 120 | 4 | 3.33% | Visual Spoofing ASR (Unauthorized Claim Image) |
| B | `none_empty` | No-document control | 120 | 120 | 0 | 0.00% |  |
| B | `claim_image_authorized` | Authorized control | 120 | 120 | 120 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| B | `claim_image_wrong_scope` | Scope control | 120 | 120 | 7 | 5.83% |  |
| B | `none_authorized` | Authorized baseline | 120 | 120 | 120 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |

## Table 2: Paired Causal Contrasts (Percentage Points & 95% Cluster Bootstrap CI)

| Track | Contrast | Complete Pairs | Estimate (pp) | 95% Cluster CI (pp) | p_raw | p_Holm |
|---|---|---:|---:|---|---:|---:|
| A | Primary Image Claim (`claim_image - neutral_image`) | 120 | +0.00 | [+0.00, +0.00] | 1.0000 | 1.0000 |
| A | Transcript Claim (`claim_text - neutral_text`) | 120 | +0.00 | [+0.00, +0.00] | — | — |
| A | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 120 | +99.17 | [+97.50, +100.00] | — | — |
| B | Primary Image Claim (`claim_image - neutral_image`) | 120 | +3.33 | [+0.83, +5.83] | 0.1227 | 0.2453 |
| B | Transcript Claim (`claim_text - neutral_text`) | 120 | +1.67 | [+0.00, +5.00] | — | — |
| B | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 120 | +94.17 | [+90.00, +97.50] | — | — |
