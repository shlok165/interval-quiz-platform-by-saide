# Lab 9 — Before / After Comparison (computed)

_Before:_ Lab 7, 7 Task 1 / 7 Task 2 automated records, 2026-09-30  
_After:_ Lab 9, 5 automated fixture runs, 2026-10-12

These files record scripted browser execution, not an observed human usability study. Fixture IDs identify runs/accounts, not verified participants.

## 1. Headline

| Metric | Lab 7 (before) | Lab 9 (after) | Change |
|---|---|---|---|
| **Task 1 — recorded completion** | 0/7 (0%) | 5/5 (100%) | **+100 pts** |
| **Task 2 — recorded completion** | 0/7 (0%) | 5/5 (100%) | **+100 pts** |
| Task 1 median time | 38.2 s (failed runs) | 6.2 s (to completion) | — |
| Task 2 median time | 67.5 s (failed runs) | 4.8 s | — |
| Task 1 blocking errors / run | 2.0 | 0.0 | **-2.0** |
| Task 2 blocking errors / run | 4.0 | 0.0 | **-4.0** |

> Lab 7's durations are elapsed times for failed runs, including timeout waits; Lab 9's are elapsed times for successful scripted runs, including setup and login. They are reported for traceability, not as evidence of faster human task completion.

## 2. Numerical checks on the automated run

The original T1–T4 thresholds are shown for traceability. Meeting a numeric threshold in automation is not evidence of unassisted human completion or human task time. Human validation remains unmeasured. T4 checks the maximum per-run error count, not the mean.

| Check | Threshold | Automated observation | Numeric check |
|---|---|---|---|
| T1 Task 1 completion | ≥ 90% | 5/5 = 100% | Within threshold |
| T2 Task 2 completion | 100% | 5/5 = 100% | Within threshold |
| T3 Task 2 execution time | median ≤ 180 s, all ≤ 240 s; all runs complete | median 4.8 s, max 6.0 s | Within threshold |
| T4 Task 1 recorded blocking errors | ≤ 1 per run | max 0, mean 0.0, total 0 | Within threshold |

## 3. Per-fixture automated results

Task 1 uses the shared instructor account; Task 2 uses the student account for each fixture ID.

| Fixture ID | Task 1 | Task 2 |
|---|---|---|
| N11 | Pass 12.2 s, 0 err, 14/14 steps | Pass 6.0 s, 0 err, 10/10 steps |
| N12 | Pass 5.7 s, 0 err, 14/14 steps | Pass 4.8 s, 0 err, 10/10 steps |
| N13 | Pass 6.5 s, 0 err, 14/14 steps | Pass 4.7 s, 0 err, 10/10 steps |
| N14 | Pass 6.2 s, 0 err, 14/14 steps | Pass 4.5 s, 0 err, 10/10 steps |
| N15 | Pass 6.1 s, 0 err, 14/14 steps | Pass 5.0 s, 0 err, 10/10 steps |

## 4. Step-level failures (after)

- none — every recorded step passed in every automated run.

## 5. Slowest scripted steps (after, mean across runs)

| Step | Mean | Max |
|---|---|---|
| `task1:login` | 2.3 s | 2.9 s |
| `task2:login` | 2.1 s | 2.3 s |
| `task2:answer-questions` | 1.4 s | 1.5 s |
| `task1:save-settings` | 0.9 s | 1.3 s |
| `task1:add-question-4-short` | 0.7 s | 1.0 s |
| `task1:published-badge` | 0.6 s | 2.0 s |
| `task1:publish` | 0.5 s | 1.2 s |
| `task1:save-exam-rules` | 0.5 s | 0.7 s |
| `task2:agree-rules` | 0.4 s | 0.4 s |
| `task1:add-question-2-multiple` | 0.4 s | 0.8 s |
| `task1:open-course` | 0.4 s | 0.6 s |
| `task2:open-course` | 0.3 s | 0.6 s |

