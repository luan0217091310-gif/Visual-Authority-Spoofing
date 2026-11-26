# VAS Benchmark Summary Tables (`EXPLORATORY_OR_DEV_LIVE`)

## Table 1: Condition-Level Event Rates, Attack Success Rate (ASR), and False Refusal Rate (FRR)

| Track | Condition (`condition_id`) | Role | Planned | Observed | Events | Event Rate (%) | Key Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| A | `neutral_text` | Text baseline | 24 | 24 | 19 | 79.17% |  |
| A | `claim_text` | Text claim | 24 | 23 | 22 | 95.65% |  |
| A | `neutral_image` | Image baseline | 24 | 24 | 20 | 83.33% | Baseline Unauthorized Rate (Neutral Image) |
| A | `claim_image` | Image claim | 24 | 24 | 19 | 79.17% | Visual Spoofing ASR (Unauthorized Claim Image) |
| A | `none_empty` | No-document control | 24 | 24 | 17 | 70.83% |  |
| A | `claim_image_authorized` | Authorized control | 24 | 24 | 24 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| A | `claim_image_wrong_scope` | Scope control | 24 | 24 | 19 | 79.17% |  |
| A | `none_authorized` | Authorized baseline | 24 | 24 | 24 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |
| B | `neutral_text` | Text baseline | 24 | 24 | 10 | 41.67% |  |
| B | `claim_text` | Text claim | 24 | 24 | 20 | 83.33% |  |
| B | `neutral_image` | Image baseline | 24 | 24 | 13 | 54.17% | Baseline Unauthorized Rate (Neutral Image) |
| B | `claim_image` | Image claim | 24 | 24 | 15 | 62.50% | Visual Spoofing ASR (Unauthorized Claim Image) |
| B | `none_empty` | No-document control | 24 | 24 | 0 | 0.00% |  |
| B | `claim_image_authorized` | Authorized control | 24 | 24 | 24 | 100.00% | Authorized Utility (False Refusal Rate = 0.00%) |
| B | `claim_image_wrong_scope` | Scope control | 24 | 24 | 3 | 12.50% |  |
| B | `none_authorized` | Authorized baseline | 24 | 24 | 24 | 100.00% | Baseline Utility (False Refusal Rate = 0.00%) |

## Table 2: Paired Causal Contrasts (Percentage Points & 95% Cluster Bootstrap CI)

| Track | Contrast | Complete Pairs | Estimate (pp) | 95% Cluster CI (pp) | p_raw | p_Holm |
|---|---|---:|---:|---|---:|---:|
| A | Primary Image Claim (`claim_image - neutral_image`) | 24 | -4.17 | [-12.50, +4.17] | — | — |
| A | Transcript Claim (`claim_text - neutral_text`) | 23 | +13.04 | [+4.17, +22.73] | — | — |
| A | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 24 | +20.83 | [+8.33, +33.33] | — | — |
| B | Primary Image Claim (`claim_image - neutral_image`) | 24 | +8.33 | [-12.50, +29.17] | — | — |
| B | Transcript Claim (`claim_text - neutral_text`) | 24 | +41.67 | [+25.00, +58.33] | — | — |
| B | Scope Control (`claim_image_authorized - claim_image_wrong_scope`) | 24 | +87.50 | [+79.17, +95.83] | — | — |
