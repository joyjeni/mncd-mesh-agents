# Table 2 (revised): Qualitative architectural comparison

Superseding `tables/table2_sota_comparison.md`. The numeric "Tool-selection benchmark" column has been
removed because the five entries drew from four incompatible tasks/datasets (MATH, HumanEval,
real ToolBench, and MNCD's own synthetic fixture) and are not directly comparable — see
`paper/review_stanford.md` Detailed Comment 1 and `paper/review_cmu.md` Detailed Comment 3.
A same-benchmark numeric comparison is planned separately (`tables/table2_same_benchmark.csv`,
see `paper/author_response.md`, Fix 1).

| Framework | Coordination | Context sharing | Fault tolerance | Replication | Distress / escalation | Consensus mechanism | Reference |
|---|---|---|---|---|---|---|---|
| AutoGen [Wu et al., COLM 2024] | Centralized GroupChat manager | Shared message log | No | No | No | Manager selects next speaker | arXiv:2308.08155 |
| MetaGPT [Hong et al., ICLR 2024 Oral] | Assembly-line SOPs | Filtered pub/sub | Partial (role retry) | No | No | SOP-defined role handoff | ICLR 2024 / arXiv:2308.00352 |
| CAMEL [Li et al., NeurIPS 2023] | Role-playing pair | Inception prompting | No | No | No | Turn-based dialogue, no aggregation | NeurIPS 2023 |
| LangGraph [LangChain, 2024] | Directed graph | State channels | Checkpoints | No (single state) | No | Graph-conditional routing | langchain.com/langgraph |
| ToolLLaMA [Qin et al., ICLR 2024] | Single-agent DFSDT | n/a | n/a | n/a | n/a | Single-agent search, no aggregation | ICLR 2024 / arXiv:2307.16789 |
| **MNCD (this work)** | **P2P mesh + gossip** | **Topic pub/sub + gossip [Demers 1987]** | **Yes (measured 97.0% acc. with 2/5 dead)** | **Yes (R=3, measured coverage 2.60–3.00)** | **Present in code (τ=0.55); trigger rate 0.0000 in all reported experiments — see Weaknesses in both reviews** | **Weighted score-sum across agents (see Fix note below — not rank-based Borda as originally described)** | **this paper** |

**Note on the MNCD row (added per peer review):** two entries above are qualified rather than stated
unconditionally, in contrast to the original Table 2's unqualified bold claims: (1) the distress column
reports the mechanism's *presence in code*, not a demonstrated function, because its measured trigger rate
across all six reported scenarios is 0.0000 (see `metrics/results.json` and `paper/review_stanford.md`
Weaknesses); (2) the consensus mechanism is described as it is actually implemented
(`src/agents.py::consensus_pick`, a weighted sum of raw scores), not as the rank-based Borda formula
originally stated in `README.md`'s "Core Equations" section, per `paper/review_cmu.md` Detailed Comment 2.
