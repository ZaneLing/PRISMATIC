# v0.10: author-core comparison and scoped-skill reflection

## Executed common-data comparison (seed 42)

Backbone: DeepSeek-V4.1-Flash. Test: 988 scenario-group-held-out RxSafeBench derived option questions. These are methods on a common task, not a model leaderboard.

| Method | Correct / 988 | Accuracy | RxQA OpenFDA, correct / 300 |
|---|---:|---:|---:|
| CoT | 467 | 47.27% | 193 (64.33%) |
| GRASP author core + task adapter | 502 | 50.81% | 189 (63.00%) |
| RxRSI, scoped language skills | 467 | 47.27% | 193 (64.33%) |

The GRASP core is pinned and unmodified. This is its application to our new task, not an original MedAgentBench score. The original core uses balanced training probes and 387-case best-checkpoint validation. Scoped RxRSI uses the 190-case proposal / 197-case guard protocol; costs and selection mechanisms differ. Actor cap is 512; both updated implementations use a 3,072-token proposal cap.

GRASP repairs 102 CoT errors and regresses 67 correct answers, for +3.54 percentage points; the descriptive paired scenario-cluster 95% interval is [0.91, 6.07] points. Its RxQA transfer is lower. Independent recount and case alignment pass.

## What failed in our update

All four scoped-skill rounds are rejected. Proposed rules usually match zero proposal cases, with only 0–3 activations per candidate, so the final library remains empty. Its test curve is exactly flat and removing routing changes nothing. This is a measured failure, not successful RSI.

A training-only audit also finds no wrong answer with a unique evidence-mentioned option equal to GT, so a simple letter/name remapping is not supported as the main remedy.

## Continued iteration

v0.11 adds auditable drug-label evidence. It first measures label coverage and development utility, then compares fixed retrieval with feedback-selected configurations using the same evidence access. This addresses knowledge grounding rather than adding more untested reflections. All learned clinical text remains research artifacts; no clinical-safety claim is made.
