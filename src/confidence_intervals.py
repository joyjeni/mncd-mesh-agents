"""Wilson 95% confidence intervals for the MNCD scenario accuracies (added after the 2026-11 postdoc review).

Accuracy on n queries is a binomial proportion; with n = 15 (Karnataka scenarios) the interval is very wide,
so differences between scenarios must be read with their intervals, not as point estimates.
Usage: python src/confidence_intervals.py  ->  tables/table1_with_ci.md
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def wilson(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def main() -> None:
    data = json.loads((ROOT / "metrics" / "results.json").read_text())["scenarios"]
    rows = ["| Scenario | n queries | Accuracy | Wilson 95% CI | CI width |", "|---|---|---|---|---|"]
    for name, s in data.items():
        n, p = int(s["total_queries"]), float(s["accuracy"])
        lo, hi = wilson(p, n)
        rows.append(f"| {name} | {n} | {100*p:.1f}% | [{100*lo:.1f}%, {100*hi:.1f}%] | {100*(hi-lo):.1f} pp |")
    note = ("\n\nAgents are simulated with a fixed competence parameter, so these accuracies measure the "
            "aggregation protocol under that model, not LLM quality. Scenarios with n = 15 cannot separate "
            "methods that differ by less than ~30 pp; a publishable comparison needs n >= 300 per arm.\n")
    out = ROOT / "tables" / "table1_with_ci.md"
    out.write_text("\n".join(rows) + note)
    print(out.read_text())


if __name__ == "__main__":
    main()
