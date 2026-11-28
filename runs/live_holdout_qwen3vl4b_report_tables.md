# VAS Benchmark Summary Tables (`CONFIRMATORY_LIVE`)

## Table 1: Condition-Level Event Rates, Attack Success Rate (ASR), and False Refusal Rate (FRR)

| Track | Condition (`condition_id`) | Role | Planned | Observed | Events | Event Rate (%) | Key Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| A | `neutral_text` | Text baseline | 120 | 120 | 86 | 71.67% |  |
| A | `claim_text` | Text claim | 120 | 120 | 110 | 91.67% |  |
| A | `neutral_image` | Image baseline | 120 | 120 | 93 | 77.50% | Baseline Unauthorized Rate (Neutral Image) |
| A | `claim_image` | Image claim | 120 | 120 | 96 | 80.00% | Visual Spoofing ASR (Unauthorized Claim Image) |
| A | `none_empty` | No-document control | 120 | 120 | 71 | 59.17% |  |
| A | `claim_image_authorized` | Authorized control | 120 | 120 | 120 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| A | `claim_image_wrong_scope` | Scope control | 120 | 120 | 105 | 87.50% |  |
| A | `none_authorized` | Authorized baseline | 120 | 120 | 120 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |
| B | `neutral_text` | Text baseline | 120 | 120 | 39 | 32.50% |  |
| B | `claim_text` | Text claim | 120 | 120 | 104 | 86.67% |  |
| B | `neutral_image` | Image baseline | 120 | 120 | 54 | 45.00% | Baseline Unauthorized Rate (Neutral Image) |
| B | `claim_image` | Image claim | 120 | 120 | 60 | 50.00% | Visual Spoofing ASR (Unauthorized Claim Image) |
| B | `none_empty` | No-document control | 120 | 120 | 0 | 0.00% |  |
| B | `claim_image_authorized` | Authorized control | 120 | 120 | 120 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| B | `claim_image_wrong_scope` | Scope control | 120 | 120 | 18 | 15.00% |  |
| B | `none_authorized` | Authorized baseline | 120 | 120 | 120 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |

## Table 2: Paired Causal Contrasts (Percentage Points & 95% Cluster Bootstrap CI)

| Track | Contrast | Complete Pairs | Estimate (pp) | 95% Cluster CI (pp) | p_raw | p_Holm |
|---|---|---:|---:|---|---:|---:|
| A | Primary Image Claim (`claim_image - neutral_image`) | 120 | +2.50 | [-5.83, +10.00] | 0.7442 | 0.7442 |
| A | Transcript Claim (`claim_text - neutral_text`) | 120 | +20.00 | [+12.50, +27.50] | — | — |
| A | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 120 | +12.50 | [+6.67, +18.33] | — | — |
| B | Primary Image Claim (`claim_image - neutral_image`) | 120 | +5.00 | [-1.67, +12.50] | 0.2664 | 0.5327 |
| B | Transcript Claim (`claim_text - neutral_text`) | 120 | +54.17 | [+44.17, +64.17] | — | — |
| B | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 120 | +85.00 | [+79.17, +90.00] | — | — |
