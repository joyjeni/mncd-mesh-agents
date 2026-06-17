# MNCD — Mesh Network Context Diffusion

> **PhD Objective 3** | Fault-Tolerant Multi-Agent LLM Mesh for Agricultural AI

[![GitHub](https://img.shields.io/badge/GitHub-Public-black)](https://github.com/joyjeni/mncd-mesh-agents)
[![Kaggle](https://img.shields.io/badge/Kaggle-Notebook-blue)](https://www.kaggle.com)
[![data.gov.in](https://img.shields.io/badge/data.gov.in-Karnataka%20APMC-orange)](https://data.gov.in)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**GitHub**: https://github.com/joyjeni/mncd-mesh-agents (PUBLIC — previously private, now open)

---

## What is MNCD?

MNCD (**Mesh Network Context Diffusion**) is a fault-tolerant multi-agent architecture where LLM agents are arranged in a mesh topology and communicate via a **publish/subscribe + gossip** protocol with **replication factor R=3**. Unlike hub-and-spoke or chain architectures, MNCD has no single point of failure: if agents die or the network suffers packet loss, the mesh re-routes queries through surviving agents using Borda consensus across available responses.

**Novel Contribution**: MNCD is the first system to combine all four of the following in a single multi-agent LLM stack:
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

When R=3 agents return responses to the same query, MNCD aggregates them via Borda count:

$$\text{score}_{\text{Borda}}(r) = \sum_{a \in \mathcal{A}} \left(|\mathcal{C}| - \text{rank}_a(r)\right)$$

where $\mathcal{C}$ is the candidate response set and $\text{rank}_a(r)$ is agent $a$'s ranking of response $r$. The highest-scoring response is selected as the final output.

### Distress Trigger

An agent broadcasts a **distress signal** on the dedicated distress channel when its confidence falls below threshold:

$$c < \tau = 0.55$$

On receiving a distress signal, the mesh automatically re-routes the query to a backup agent set and increases replication factor to R=5 for that query.

---

## Results

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

S5 uses 15 live Karnataka APMC mandi queries sourced from data.gov.in. The mesh distributes these queries across specialised agents (price lookup, market availability, crop advisory).

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
│   ├── mesh.py              # Mesh topology, pub/sub, gossip
│   ├── agent.py             # Agent base class (confidence scoring)
│   ├── consensus.py         # Borda aggregation
│   ├── distress.py          # Distress channel logic (c < τ=0.55)
│   ├── replication.py       # R=3 redundant dispatch
│   └── context_bus.py       # Message envelope + user_language broadcast
├── experiments/
│   ├── scenario_s1.py       # Baseline
│   ├── scenario_s2.py       # Full mesh
│   ├── scenario_s3.py       # 2/5 agents dead
│   ├── scenario_s4.py       # 20% packet loss
│   └── scenario_s5.py       # Karnataka APMC real data
├── kaggle/
│   └── mncd_mesh.ipynb      # Reproducible benchmark
└── docs/
    └── README_OBJ3.md       # This file
```

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
