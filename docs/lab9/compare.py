#!/usr/bin/env python3
"""Lab 9 — compute the before/after comparison and emit report tables.

Reads docs/lab7/results.json (before) and docs/lab9/results.json (after) and writes
docs/lab9/comparison.md with the numbers the report's before/after section needs.
Every figure is computed, not asserted.
"""
from __future__ import annotations

import json
import os
import statistics as stats
from pathlib import Path

DOCS = Path(__file__).resolve().parent          # docs/lab9
ROOT_DOCS = DOCS.parent                         # docs
LAB7 = ROOT_DOCS / "lab7" / "results.json"
LAB9 = DOCS / "results.json"
OUT = DOCS / "comparison.md"


def load(path: Path):
    if not path.exists():
        raise SystemExit(f"missing {path}")
    return json.loads(path.read_text())


def agg(rows):
    ok = [r for r in rows if r.get("completed")]
    times = [r["time_ms"] for r in rows]
    errors = [r.get("errors", 0) for r in rows]
    # Lab 7 rows have no completed_steps — filter Nones so mean() does not choke.
    steps_done = [r.get("completed_steps") or 0 for r in rows]
    steps_total = [r.get("total_steps") or 0 for r in rows]
    return {
        "n": len(rows),
        "success": len(ok),
        "rate": (len(ok) / len(rows) * 100) if rows else 0.0,
        "mean_ms": stats.mean(times) if times else 0,
        "median_ms": stats.median(times) if times else 0,
        "min_ms": min(times) if times else 0,
        "max_ms": max(times) if times else 0,
        "blocking_mean": stats.mean(errors) if errors else 0,
        "blocking_total": sum(errors),
        "blocking_max": max(errors) if errors else 0,
        "steps_mean": stats.mean(steps_done) if steps_done else 0,
        "steps_total": steps_total[0] if steps_total else 0,
    }


def s(ms):
    return f"{ms / 1000:.1f} s"


def fmt_pct(x):
    return f"{x:.0f}%"


def comparison_data():
    """Load and normalise the two recorded automated runs for all report outputs."""
    before = load(LAB7)
    after = load(LAB9)

    # Lab 7 records one object per (tester, task); Lab 9 nests tasks per tester.
    b_t1 = [r for r in before["results"] if "Task1" in r["task"]]
    b_t2 = [r for r in before["results"] if "Task2" in r["task"]]
    a_t1 = [t["task1"] for t in after["testers"]]
    a_t2 = [t["task2"] for t in after["testers"]]

    # normalise the Lab 7 shape onto the Lab 9 keys
    def norm7(r):
        return {
            "completed": r["completed"],
            "time_ms": r["durationMs"],
            "errors": len(r["errors"]),
            "completed_steps": None,
            "total_steps": None,
        }

    b_t1 = [norm7(r) for r in b_t1]
    b_t2 = [norm7(r) for r in b_t2]

    B1, B2 = agg(b_t1), agg(b_t2)
    A1, A2 = agg(a_t1), agg(a_t2)

    return dict(before=before, after=after, B1=B1, B2=B2, A1=A1, A2=A2)


def thresholds(A1, A2):
    """Numerical checks only; browser automation cannot validate human UX targets."""
    return {
        "T1": A1["n"] > 0 and A1["rate"] >= 90,
        "T2": A2["n"] > 0 and A2["rate"] == 100,
        "T3": A2["n"] > 0 and A2["success"] == A2["n"]
        and A2["median_ms"] <= 180_000 and A2["max_ms"] <= 240_000,
        "T4": A1["n"] > 0 and A1["blocking_max"] <= 1,
    }


def main() -> None:
    data = comparison_data()
    before, after = data["before"], data["after"]
    B1, B2, A1, A2 = (data[k] for k in ("B1", "B2", "A1", "A2"))
    checks = thresholds(A1, A2)
    lines: list[str] = []
    w = lines.append
    w("# Lab 9 — Before / After Comparison (computed)\n")
    w(f"_Before:_ Lab 7, {B1['n']} Task 1 / {B2['n']} Task 2 automated records, {before['generatedAt'][:10]}  ")
    w(f"_After:_ Lab 9, {len(after['testers'])} automated fixture runs, {after.get('run_at', '')[:10]}\n")
    w("These files record scripted browser execution, not an observed human usability study. "
      "Fixture IDs identify runs/accounts, not verified participants.\n")

    # ---------------------------------------------------------------- headline
    w("## 1. Headline\n")
    w("| Metric | Lab 7 (before) | Lab 9 (after) | Change |")
    w("|---|---|---|---|")
    w(
        f"| **Task 1 — recorded completion** | {B1['success']}/{B1['n']} ({fmt_pct(B1['rate'])}) | "
        f"{A1['success']}/{A1['n']} ({fmt_pct(A1['rate'])}) | "
        f"**{A1['rate'] - B1['rate']:+.0f} pts** |"
    )
    w(
        f"| **Task 2 — recorded completion** | {B2['success']}/{B2['n']} ({fmt_pct(B2['rate'])}) | "
        f"{A2['success']}/{A2['n']} ({fmt_pct(A2['rate'])}) | "
        f"**{A2['rate'] - B2['rate']:+.0f} pts** |"
    )
    w(
        f"| Task 1 median time | {s(B1['median_ms'])} (failed runs) | "
        f"{s(A1['median_ms'])} (to completion) | — |"
    )
    w(
        f"| Task 2 median time | {s(B2['median_ms'])} (failed runs) | "
        f"{s(A2['median_ms'])} | — |"
    )
    w(
        f"| Task 1 blocking errors / run | {B1['blocking_mean']:.1f} | "
        f"{A1['blocking_mean']:.1f} | **{A1['blocking_mean'] - B1['blocking_mean']:+.1f}** |"
    )
    w(
        f"| Task 2 blocking errors / run | {B2['blocking_mean']:.1f} | "
        f"{A2['blocking_mean']:.1f} | **{A2['blocking_mean'] - B2['blocking_mean']:+.1f}** |"
    )
    w("")
    w(
        "> Lab 7's durations are elapsed times for failed runs, including timeout waits; Lab 9's "
        "are elapsed times for successful scripted runs, including setup and login. They are "
        "reported for traceability, not as evidence of faster human task completion.\n"
    )

    # ---------------------------------------------------------------- targets
    w("## 2. Numerical checks on the automated run\n")
    w("The original T1–T4 thresholds are shown for traceability. Meeting a numeric threshold "
      "in automation is not evidence of unassisted human completion or human task time. "
      "Human validation remains unmeasured. T4 checks the maximum per-run error count, not the mean.\n")
    w("| Check | Threshold | Automated observation | Numeric check |")
    w("|---|---|---|---|")
    verdict = lambda key: "Within threshold" if checks[key] else "Not satisfied"
    w(f"| T1 Task 1 completion | ≥ 90% | {A1['success']}/{A1['n']} = {fmt_pct(A1['rate'])} | {verdict('T1')} |")
    w(f"| T2 Task 2 completion | 100% | {A2['success']}/{A2['n']} = {fmt_pct(A2['rate'])} | {verdict('T2')} |")
    w(
        f"| T3 Task 2 execution time | median ≤ 180 s, all ≤ 240 s; all runs complete | median {s(A2['median_ms'])}, "
        f"max {s(A2['max_ms'])} | {verdict('T3')} |"
    )
    w(
        f"| T4 Task 1 recorded blocking errors | ≤ 1 per run | max {A1['blocking_max']}, "
        f"mean {A1['blocking_mean']:.1f}, total {A1['blocking_total']} | {verdict('T4')} |"
    )
    w("")

    # ---------------------------------------------------------------- per run
    w("## 3. Per-fixture automated results\n")
    w("Task 1 uses the shared instructor account; Task 2 uses the student account for each fixture ID.\n")
    w("| Fixture ID | Task 1 | Task 2 |")
    w("|---|---|---|")
    for t in after["testers"]:
        a, b = t["task1"], t["task2"]
        w(
            f"| {t['id']} | "
            f"{'Pass' if a['completed'] else 'Fail'} {s(a['time_ms'])}, {a['errors']} err, "
            f"{a.get('completed_steps', '?')}/{a.get('total_steps', '?')} steps | "
            f"{'Pass' if b['completed'] else 'Fail'} {s(b['time_ms'])}, {b['errors']} err, "
            f"{b.get('completed_steps', '?')}/{b.get('total_steps', '?')} steps |"
        )
    w("")

    # ---------------------------------------------------------------- per step
    w("## 4. Step-level failures (after)\n")
    any_fail = False
    for t in after["testers"]:
        for task_key, label in (("task1", "Task 1"), ("task2", "Task 2")):
            for st_ in t[task_key]["steps"]:
                if not st_["pass"]:
                    any_fail = True
                    err = (st_.get("error") or "").replace("\n", " ")[:160]
                    w(f"- **{t['id']} / {label} / `{st_['name']}`** — {err}")
    if not any_fail:
        w("- none — every recorded step passed in every automated run.")
    w("")

    # ---------------------------------------------------------------- friction
    w("## 5. Slowest scripted steps (after, mean across runs)\n")
    buckets: dict[str, list[float]] = {}
    for t in after["testers"]:
        for task_key in ("task1", "task2"):
            for st_ in t[task_key]["steps"]:
                key = f"{task_key}:{st_['name']}"
                buckets.setdefault(key, []).append(st_["ms"])
    top = sorted(buckets.items(), key=lambda kv: -stats.mean(kv[1]))[:12]
    w("| Step | Mean | Max |")
    w("|---|---|---|")
    for k, v in top:
        w(f"| `{k}` | {s(stats.mean(v))} | {s(max(v))} |")
    w("")

    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")
    print(f"T1 {A1['success']}/{A1['n']} rate={A1['rate']:.0f}% mean_err={A1['blocking_mean']:.1f}")
    print(f"T2 {A2['success']}/{A2['n']} rate={A2['rate']:.0f}% median={s(A2['median_ms'])} max={s(A2['max_ms'])}")
    print(f"automated numerical checks: {checks}; human usability targets: not evaluated")


if __name__ == "__main__":
    main()
