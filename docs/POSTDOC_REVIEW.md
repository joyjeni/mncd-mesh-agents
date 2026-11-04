# Postdoctoral review — O3 — MNCD (mesh consensus)

Reviewer stance: a postdoctoral researcher preparing this chapter for a Q1 journal (November 2026).
Severity: **Critical** blocks publication · **Major** a reviewer will require it · **Fixed** done in this commit.

| Severity | Finding | Evidence | Action |
|---|---|---|---|
| Critical | Accuracy is a property of the simulator, not of agents | Agents answer correctly with a fixed `competence` probability; with replication R = 3 the 97 % accuracy follows from the binomial majority formula. No LLM is in the loop. | Run with real open-weight LLM agents (and inject hallucinating peers); report accepted-error rate and abstention, as in the ACRS master O3 experiments. |
| Critical | Karnataka scenarios use 15 queries | 93.3 % vs 53.3 % on n = 15 has Wilson 95 % intervals [70.2, 98.8] and [30.1, 75.2] — they overlap. | Added `src/confidence_intervals.py` → `tables/table1_with_ci.md`. Collect ≥ 300 real farmer queries (AgriToolBench-IN). |
| Major | Consensus rule differs from the thesis | This repo aggregates by score-sum; the ACRS master uses an evidence-weighted quorum with a safety proof (b ≤ f, n ≥ 3f + 1). | Port the evidence-weighted quorum and its adversary tests (forged citations, collusion) here, or state clearly that score-sum is the lab variant. |
| Major | "Byzantine" / fault-tolerance claims | Node failure and packet loss are crash faults, not Byzantine faults. | Use "crash-fault tolerant" for S3/S4; reserve "Byzantine" for the adversarial experiments. |

## What this chapter needs to be journal-ready

1. Real LLM agents (open-weight 7–8B class) instead of simulated ones, with ≥ 300 evaluation items per arm.
2. At least two recognised public benchmarks (see the dataset plan in `phd-agentic-ai-master/docs/POSTDOC_ROADMAP.md`).
3. Pre-registered primary metric and one headline statistical test; all other comparisons labelled exploratory.
4. Leak-free splits and a reproducibility command that regenerates every table.
