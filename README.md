# MNCD — Mesh Network Context Diffusion (ACRS objective O4: Byzantine-tolerant coordination for certified execution)

> **Ph.D. CSE, M S Ramaiah University of Applied Sciences (FET).**  
> Scholar: Jenisha T (`24ETRP720001`). Supervisor: Dr. Padma Priya Dharishini P.  
> ACRS objectives in the order they act: O1 session-adaptive tool scoring (SATR) → O2 PID-controlled provenance pruning (FCNP) → O3 risk-weighted policy routing (APRR) → **O4 certified execution (MNCD)**, with G1 policy as code.

**Objective numbering.** The thesis numbers the objectives in the order in which they act within one step. Older sections of this README and the notebooks call this work "Objective 3"; in the thesis it is **O4**.

## Latest: ACRS on AppWorld (November 2026)

In ACRS the mesh vote moves from "which tool" to "which outcome". On [AppWorld](https://github.com/StonyBrookNLP/appworld) (Trivedi et al., ACL 2024: 9 apps, 457 APIs, tasks graded by state-based unit tests), when a proposed code block would change the world, O4 samples further candidate programs, saves the world state, runs every candidate from that state, records the state-changing calls each one made and whether it raised an error, and restores the state and the agent's variables after each run. With three candidates, the outcome with the largest share of clean runs is certified if the share reaches 0.5 with at least two supporters, and only then is it executed for real; otherwise ACRS abstains and the agent is told why. Login steps are exempt. Before anything runs, G1 (policy as code) denies deletions the task does not ask for, writes outside the task's apps, and ids or e-mail addresses the agent never observed.

**Development split, first full run** (57 tasks in 19 scenarios, one seed; Qwen3-8B and Qwen3-4B in 4-bit AWQ on two free T4 GPUs; Kaggle: seven configurations in 10 h 32 min, the run without O3 in a second session of 131 min). Aggregates only: AppWorld task text and API outputs are not published.

| Configuration | Task success (TGC) | Scenarios (SGC) | Tokens (M) | Wall (min) | Collateral damage |
|---|---|---|---|---|---|
| Reference agent (8B on every step, no ACRS part) | 19.3 % (11/57) | 1/19 | 3.39 | 58 | 0/57 |
| **Full ACRS** | **17.5 % (10/57)** | **3/19** | **3.36** | **123** | **0/57** |
| O2 only | 15.8 % (9/57) | 1/19 | 2.22 | 34 | 0/57 |
| Full without O1 | 10.5 % (6/57) | 0/19 | 2.48 | 88 | 0/57 |
| Full without O2 | 19.3 % (11/57) | 2/19 | 4.16 | 145 | 0/57 |
| Full without O3 | 14.0 % (8/57) | 1/19 | 3.14 | 131 | 0/57 |
| Full without O4 | 14.0 % (8/57) | 0/19 | 1.38 | 47 | 1/57 |
| Full without G1 | 12.3 % (7/57) | 0/19 | 3.57 | 129 | 0/57 |

What the run shows for O4 (RQ4):

- In full ACRS, 309 state-changing steps were put to a vote: 58 were certified and committed, 26 were withheld because the candidates disagreed, and in 225 every candidate raised an error, so nothing was executed.
- No collateral damage in any configuration with O4, against one task (1/57) without it. This is a safety signal resting on a single event.
- Certification is costly: full ACRS used 2.4 times the tokens and 2.6 times the wall time of the same system without O4.
- With three candidates per vote, the quorum bound in the thesis tolerates no faulty candidate (f = 0), so this vote is an agreement check between candidates, not a Byzantine guarantee; the guarantee needs at least four candidates.
- G1 made no denial in this split, so it is not yet tested on AppWorld.
- Status: signal only; tasks with planted faults and unsafe instructions, votes with at least four candidates, and a cheaper vote are needed before RQ4 can be answered.

No configuration differs significantly in task success on 57 tasks (every McNemar p ≥ 0.34; full ACRS against full without O4: 4 tasks against 2, p = 0.688); the test splits will be run with three seeds. The released harness uses the earlier numbering in its configuration names (`no_o3` is the run without O4).

**Security controls in the harness (policy as code).** Deny by default; every condition must hold; each rule traced to a source and tested in both directions; exportable to OPA Rego.

| Rule | What it enforces |
|---|---|
| `R-AW-DEL` | A delete-type call runs only if the task asks to delete or remove. |
| `R-AW-SCOPE` | Writes only to apps the task allows. |
| `R-AW-PROV` | An id, e-mail address or phone number written by a state-changing call must have been observed in the task or an earlier result. |
| `R-COMMIT-01` | Commit an answer only when it is certified, the quorum holds, no quarantined evidence is used and no stage failed (fail closed). |
| `R-EXEC-01` | A peer may call only a read-only tool that O1 committed for the sub-goal (least privilege). |
| `R-EXEC-02` | A state-changing tool runs only after a named person approved that exact call. |
| `R-MEM-01` | Only successful, non-quarantined observations enter the next turn's context and O1's session prior. |
| `R-REL-01` | A release is promoted by a named approver after the evaluation gate passed on a pinned manifest. |

- Code: [joyjeni/acrs-appworld, branch `o4-provenance`](https://github.com/joyjeni/acrs-appworld/tree/o4-provenance)
- Dashboard: the Next.js app in [`dashboard/`](dashboard/) shows the AppWorld results first, then the earlier mesh results; aggregate data in [`dashboard/public/data/appworld_dev.json`](dashboard/public/data/appworld_dev.json).
- The dashboard no longer loads `polyfill.io` (that domain was taken over in 2024 and served malicious code).

## Earlier work: the decentralised mesh (June 2026)

The rest of this README documents MNCD as developed before AppWorld, with simulated agents.


> **Postdoctoral review (November 2026) — read first.** 2 critical issue(s) affect the results reported below; see [`docs/POSTDOC_REVIEW.md`](docs/POSTDOC_REVIEW.md) before citing any number from this repository.

This repository is the **consensus-and-execution chapter** of ACRS. Agents gossip
`(toolId, score)` on a mesh, aggregate by **score-sum** (`consensus_pick`; Borda
exists as `consensus_pick_borda` and is **not** the evaluation default), then
execute only live `data.gov.in` resources whose UUIDs and GODL-India / NIC
provenance have been verified.

**Proposal-stage stance:** accuracy percentages, “2 of 5 agents down” survival
figures, and synthetic-fixture scores are **not** commitments of the research
proposal. The unit of publication is the protocol plus the live-citation contract.

## SOTA this chapter is written against

- Wu et al., AutoGen, ICLR 2024 LLM Agents Workshop / COLM 2024, arXiv:2308.08155.
- Hong et al., MetaGPT, ICLR 2024.
- Qian et al., ChatDev, ACL 2024, arXiv:2307.07924.
- Li et al., CAMEL, NeurIPS 2023.

**Gap (G3).** Those systems coordinate over natural-language messages, not over
tool identifiers backed by a ministry API.

**Novelty.** Vote object = tool ID. Fail-loud live OGD (retry 5xx/429; never
invent prices). Agriculture lock for the demonstration corpus.

---

## What is MNCD?

MNCD (**Mesh Network Context Diffusion**) is a multi-agent architecture where LLM
agents sit on a mesh and communicate via publish/subscribe plus gossip with
replication factor R=3. Unlike hub-and-spoke or chain architectures, there is no
single planner as the vote object: agents publish `(toolId, score)` and
`consensus_pick()` aggregates by **weighted score-sum**.

A true rank-based Borda implementation exists as `consensus_pick_borda()` for
comparison and is **not** the default. Do not describe the default as Borda.

**Proposal-stage:** synthetic “97%” style figures in older revisions are not
commitments of the Ph.D. proposal.

**Novel Contribution**: relative to AutoGen, MetaGPT, CAMEL, and LangGraph (see "Related Work" comparison in the paper), MNCD is, to our knowledge, the first system to combine all four of the following specifically for LLM agent meshes (a narrower and more defensible claim than "first in the literature," since pub/sub, gossip, replication, and confidence-gated escalation are individually decades-old distributed-systems primitives — see `paper/mncd_paper.tex` §Related Work and `paper/review_stanford.md` Detailed Comment 5):
1. **Pub/Sub messaging** — topic-based agent subscriptions for domain routing
2. **Gossip protocol** — decentralised state propagation with bounded convergence
3. **Replication (R=3)** — each query is processed redundantly by 3 agents; responses are aggregated
4. **Distress channel** — automatic escalation when agent confidence falls below threshold τ

---

## Deployment

**GitHub Repository**: https://github.com/joyjeni/mncd-mesh-agents

### Kaggle Notebook

`mncd_mesh.ipynb` — full reproducible benchmark including all 5 scenarios (S1–S5).

#### HuggingFace Models Used in Notebook

The notebook supports three interchangeable LLM backends. Load any of these from HuggingFace Hub:

| Model                        | HF Model ID                               | VRAM   | Notes                         |
|------------------------------|-------------------------------------------|--------|-------------------------------|
| Gemma 2 2B Instruct          | `google/gemma-2-2b-it`                    | ~5 GB  | https://huggingface.co/google/gemma-2-2b-it |
| Qwen 2.5 7B Instruct         | `Qwen/Qwen2.5-7B-Instruct`               | ~15 GB | Strong multilingual ability   |
| Llama 3.1 8B Instruct        | `meta-llama/Llama-3.1-8B-Instruct`       | ~16 GB | Requires HF token acceptance  |

```python
# Switch model in notebook:
MODEL_ID = "google/gemma-2-2b-it"          # or Qwen or Llama below
# MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
# MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

from transformers import AutoTokenizer, AutoModelForCausalLM
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map="auto")
```

---

## Core Equations

### Edge Weight (Context Routing)

$$w(p, q) = \alpha \cdot s_{pq} + (1 - \alpha) \cdot \frac{1}{1 + \ell_{pq}}$$

where:
- $s_{pq}$ — semantic similarity between agent $p$'s context and agent $q$'s topic subscription
- $\ell_{pq}$ — network latency between agents $p$ and $q$ (normalised)
- $\alpha \in [0,1]$ — trade-off between semantic fit and low latency

### Weighted score-sum consensus (response aggregation)

When R=3 agents return responses to the same query, MNCD aggregates them via a **weighted score-sum vote** (the function actually named `consensus_pick()` in `src/agents.py`):

$$\text{score}(r) = \sum_{a \in \mathcal{A}} w_a \cdot s_a(r)$$

where $s_a(r)$ is agent $a$'s raw confidence score for response $r$ and $w_a$ is agent $a$'s consensus weight. The highest-scoring response is selected as the final output.

**Correction (post-peer-review):** this README previously described the mechanism above as "Borda count" using the rank-based formula $\text{score}_{\text{Borda}}(r) = \sum_a (|\mathcal{C}| - \text{rank}_a(r))$. That formula was never implemented; the code sums raw scores, not ranks — a materially different, non-scale-invariant aggregation rule. A true rank-based Borda implementation now also exists as `consensus_pick_borda()` in `src/agents.py` for comparison; on the same 200-query synthetic fixture it scores 96.5% vs. the score-sum version's 97.5% (both well above the S1 baseline's 44.0%, confirming the choice of aggregation rule is a second-order effect relative to ensembling itself).

### Distress Trigger

An agent broadcasts a **distress signal** on the dedicated distress channel when its confidence falls below threshold:

$$c < \tau = 0.55$$

On receiving a distress signal, the mesh re-routes the query to a backup agent set for a second opinion (`Agent.handle_distress()` in `src/agents.py`).

**Correction (post-peer-review):** an earlier version of this README additionally claimed the mesh "increases replication factor to R=5 for that query" on distress. No such escalation logic exists anywhere in `src/mesh.py` — `MeshNode.R` is fixed at construction (default 3) and is never reassigned. That claim has been removed. Independent re-execution of the committed evaluation code further shows the distress channel's measured trigger rate is **0.0000 across all six reported scenarios** (see `metrics/results.json`, `distress_rate` field, and `paper/review_stanford.md` / `paper/review_cmu.md` for the root cause: `MockLLM`'s reported "confidence" is the winning score among several near-uniform draws, which is a maximum-order-statistic that is rarely below the τ=0.55 threshold regardless of correctness). A redesign of the confidence signal and a dedicated adversarial low-confidence fixture are tracked as required follow-up work — see `paper/author_response.md`.

---

## Results

**Important caveat (added post-peer-review):** every number below is produced by `MockLLM`
(`src/agents.py`), a deterministic competence-weighted random scorer, via `src/eval.py`. None of
the three HuggingFace backbones listed above (Gemma-2-2B, Qwen2.5-7B, Llama-3.1-8B) were used to
produce these committed numbers — `metrics/results.json`'s `git_commit` field is `"n/a"` and no
artifact in this repository shows the Kaggle notebook was executed. Real-backbone numbers are
planned; see `paper/author_response.md` for the committed experiment plan and timeline. Treat the
table below as a systems-layer (gossip/replication/consensus) evaluation, not an LLM-quality evaluation.

### Scenario Benchmark

| Scenario | Description                          | Task Completion |
|----------|--------------------------------------|-----------------|
| S1       | Baseline (no mesh, single agent)     | **44.0%**       |
| S2       | Full mesh, all agents alive          | **97.5%**       |
| S3       | 2/5 agents dead                      | **97.0%**       |
| S4       | 20% packet loss                      | **97.0%**       |
| S5       | Karnataka APMC real data queries     | **93.3%**       |

Key findings:
- The mesh achieves **+53.5 percentage points** over the single-agent baseline (S1 → S2).
- Fault tolerance is robust: performance degrades by only **0.5%** when 2/5 agents are dead (S2 → S3).
- The APMC-schema queries (S5) reach 93.3%; these 15 rows are synthetic, with the live schema (see Data Sources below), not live data.

---

## Data Sources

### data.gov.in — Karnataka APMC

**S5/S6 are synthetic, not live queries (corrected post-peer-review).** The live `data.gov.in`
Karnataka APMC endpoint returned no rows at evaluation time, so `src/eval.py::make_karnataka_fixture()`
generates all 15 commodity/district rows from a hardcoded Python list with the same field schema
(state, district, market, commodity, variety, grade, arrival_date, min/max/modal price). This was
previously disclosed only in the paper's Limitations section; it is stated here up front. Flipping
`USE_LIVE=True` once the live endpoint returns data is planned but not yet implemented (no such flag
currently exists in `eval.py` — it must still be added). The mesh distributes these (synthetic) queries
across specialised agents (price lookup, market availability, crop advisory).

**Expansion roadmap**:

| Region          | Status           | Resource Type              |
|-----------------|------------------|----------------------------|
| Karnataka APMC  | Synthetic fixture with the live schema | 15 mandi queries in S5 |
| Tamil Nadu APMC | Planned (Phase 2)| TN Agriculture Dept APIs   |
| Kerala APMC     | Planned (Phase 2)| VFPCK / e-market APIs      |

---

## Mesh Architecture

```
                    [Context Bus]
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Agent-1        Agent-2        Agent-3     ← Replication R=3
     (Price)       (Market)       (Advisory)
          │              │              │
          └──────[Gossip Protocol]──────┘
                         │
                    [Agent-4]  [Agent-5]   ← Backup pool
                         │
                  [Distress Channel]
                  (triggers if c < 0.55)
```

### Message Envelope Schema

```python
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class MessageEnvelope:
    topic: str                    # pub/sub topic name
    payload: Dict[str, Any]       # query data
    meta: Dict[str, Any] = field(default_factory=dict)
    # meta always includes:
    # {
    #   "user_language": "kn",    # ISO code, broadcast from translation layer
    #   "session_id": "...",
    #   "replication_set": [1,2,3],
    #   "distress": False,
    #   "confidence": 0.82
    # }
```

---

## Repository Structure

```
mncd-mesh-agents/
├── src/
│   ├── mesh.py                    # Mesh topology, pub/sub, gossip, replication, failure detection
│   ├── agents.py                  # Agent class, MockLLM backbone, consensus_pick() / consensus_pick_borda()
│   ├── eval.py                    # Evaluation harness: fixtures + S1-S6 scenario runners
│   └── ablation_homogeneous.py    # Same-model-mesh ablation (added post-peer-review)
├── notebooks/
│   └── build_notebook.py          # Generates notebooks/mncd_mesh.ipynb; defines the real HFBackbone class
├── tables/
│   ├── table1_main_results.{md,csv}
│   ├── table2_sota_comparison.{md,csv}   # superseded, see table2_qualitative.md
│   └── table2_qualitative.md             # revised qualitative comparison (post-peer-review)
├── metrics/
│   └── results.json               # S1-S6 scenario metrics (MockLLM-only; see caveat below)
├── paper/
│   ├── mncd_paper.tex
│   ├── review_stanford.md         # independent peer review (distributed systems)
│   ├── review_cmu.md              # independent peer review (agent orchestration / benchmarking)
│   └── author_response.md         # response to both reviews + examiner report
└── dashboard/                     # Next.js results dashboard (Vercel deployment)
```

*(This section previously listed an idealized/planned layout — `src/agent.py`, `consensus.py`,
`distress.py`, `replication.py`, `context_bus.py`, and a separate `experiments/` directory — that did
not match the actual repository contents. It has been corrected above to reflect the real file layout.)*

---

## Integration with PhD Pipeline

MNCD is **Objective 3** in the four-component PhD pipeline as it was numbered in June 2026 (O4 in the thesis numbering; see the top of this README):

```
[Obj2: APRR] ──routing decision──► [Obj3: MNCD] ──mesh context──► [Obj4: FCNP]
                  │                      │
           CROW neg-quality         distress
            traces as input          signals
```

### Incoming Signals

| Source       | Signal                         | Usage in MNCD                                     |
|--------------|--------------------------------|---------------------------------------------------|
| Obj2/APRR    | Routing decision (agent path)  | Determines which mesh agents receive the query    |
| Obj2/CROW    | Negative-quality CoT traces    | Used as distress signal seeds (c → low confidence)|

### Outgoing Signals

| Destination  | Signal                         | Purpose                                           |
|--------------|--------------------------------|---------------------------------------------------|
| Obj4/FCNP    | Full mesh context window       | FCNP prunes this to fit LLM token budget          |

---

## Multilingual Support

MNCD's agent logic is **system language-agnostic**: all internal processing (scoring, consensus, distress) operates on structured data and English text (post-translation).

**`user_language` is broadcast on the context bus** in every `MessageEnvelope.meta` field. This allows:
- The translation layer at the system boundary to select the correct IndicTrans2 target language for the final response.
- Per-language logging for performance analysis across S1–S5 scenarios.

Agents do **not** translate internally. They pass `meta.user_language` through unchanged.

See [`/docs/multilingual_integration.md`](./multilingual_integration.md) for the full multilingual design.

---

## Running Locally

```bash
git clone https://github.com/joyjeni/mncd-mesh-agents
cd mncd-mesh-agents
pip install -r requirements.txt

# Run scenarios S1–S6 with the MockLLM backbone (standard library only); writes metrics/results.json
python src/eval.py

# Figures and tables from metrics/results.json
python src/make_figures.py
python src/make_diagrams.py
```

S4 (20 % packet loss) depends on asyncio timing and can differ by one query between runs: the committed file has 97.0 %, two re-runs in November 2026 gave 97.5 %. The other scenarios reproduce exactly.

---

## Citation

```bibtex
@misc{mncd2026,
  title  = {MNCD: Mesh Network Context Diffusion for Fault-Tolerant Multi-Agent LLMs},
  author = {Jeni, Joy},
  year   = {2026},
  note   = {PhD Objective 3. https://github.com/joyjeni/mncd-mesh-agents}
}
```

---

*Part of the PhD Agricultural AI pipeline. See also: [Obj1 SessionRerank+](./README_OBJ1.md) | [Obj2 APRR](./README_OBJ2.md) | [Obj4 FCNP](./README_OBJ4.md) | [Multilingual Design](./multilingual_integration.md)*
