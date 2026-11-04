# MNCD — Mesh Network Context Diffusion (ACRS Objective 3)

> **Ph.D. CSE, M S Ramaiah University of Applied Sciences (FET).**  
> Scholar: Jenisha T (`24ETRP720001`). Supervisor: Dr. Padma Priya Darshini P.  
> Integrated loop: SATR → APRR → **MNCD** → FCNP.


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

### Borda Consensus (Response Aggregation)

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
- Real-world APMC data queries (S5) achieve 93.3% despite mandi price data noise and missing records.

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
| Karnataka APMC  | ✅ Integrated    | 15 mandi queries in S5     |
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

MNCD is **Objective 3** in the four-component PhD pipeline:

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

# Run all scenarios
python experiments/scenario_s1.py   # Baseline
python experiments/scenario_s2.py   # Full mesh
python experiments/scenario_s3.py   # 2/5 dead
python experiments/scenario_s4.py   # Packet loss
python experiments/scenario_s5.py   # Karnataka APMC
```

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
