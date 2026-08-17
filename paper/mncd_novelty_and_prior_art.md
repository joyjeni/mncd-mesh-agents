# MNCD — Where Decentralization Lives, and What Existed vs. What I Added

*Prepared for PhD defense / journal reviewers. Repo: [joyjeni/mncd-mesh-agents](https://github.com/joyjeni/mncd-mesh-agents)*

---

## 1. Where decentralization is implemented in the code

Decentralization in MNCD is not a design slide — it is concrete code in two files. There is no orchestrator agent, no central scheduler, and no single node that has global knowledge of the system state (the one exception, `Mesh`, is explicitly a **simulation harness**, not a system component — see §1.4).

### 1.1 `src/mesh.py` — the system layer (network, replication, failure handling)

| Mechanism | Where (function) | What it does |
|---|---|---|
| **Topic-based pub/sub** | `MeshNode.subscribe`, `MeshNode.publish`, `MeshNode._deliver_local` (lines 141–176) | Each node keeps its own local subscriber table (`self.subscriptions`). There is no broker process — publishing means "deliver to my local subscribers, then gossip to peers." |
| **Gossip / epidemic dissemination** | `MeshNode._enqueue_gossip`, `MeshNode._select_gossip_peers`, `MeshNode.gossip_round` (lines 179–235) | Every message carries a `ttl` (default 6 hops) and a dedup fingerprint. Each node independently picks `fanout=3` peers, weighted by an adaptive per-peer weight (`PeerStats.weight`, an EMA of success rate / latency), and pushes the message on. No node ever sees the full peer set beyond the ones it has met — this is the actual epidemic/push-gossip primitive. |
| **Adaptive edge weights** | `PeerStats.update` (lines 71–76) | `weight = success / (1 + latency_ms/1000)`, updated locally after every gossip exchange. This is what makes the mesh route around slow or unreliable peers without any central load balancer. |
| **Replication (fault tolerance for shared state)** | `MeshNode.replicate_put`, `replicate_get`, `replicate_accept` (lines 258–296) | Critical key/value context is written to `R` peers (default 3), chosen by the same weighted peer-selection logic, with last-write-wins versioning. No coordinator decides placement — the writing node decides using only its local peer view. |
| **Failure detection** | `MeshNode.heartbeat_tick`, `absorb_heartbeats` (lines 298–312) | Heartbeats are gossiped, not polled by a central health-check service. Each node independently marks a peer `suspected` once `now - last_seen > 4s`. Two different nodes can disagree about who is alive — this is intentional; it mirrors the classic gossip-style failure detector's *partial, non-authoritative* view. |
| **Distress / escalation channel** | `MeshNode.request_help` (lines 314–321), consumed in `agents.py` | Low-confidence agents broadcast on `__distress__`; any peer that sees it can independently choose to help. There is no assigned "backup agent" — response is opportunistic. |

### 1.2 `src/agents.py` — decentralized consensus over the mesh

| Mechanism | Where | What it does |
|---|---|---|
| **Independent tool scoring** | `Agent.select_tool` (lines 130–153) | Every agent scores tools locally with its own LLM backbone and publishes its ranking on `rank.update` — no agent asks permission or waits for a turn (contrast with turn-taking orchestration, §3). |
| **Weighted consensus (score-sum)** | `consensus_pick` (lines 175–199) | Any node that has received the same set of `rank.update` messages off the bus can independently recompute the same final answer — Σ over agents of `weight_a × confidence_a` per tool, `argmax` wins. This is what makes the "final answer" decentralized: it is not announced by an elected leader, it is *reconstructible by any peer from local gossip state*. |
| **Rank-based Borda variant** | `consensus_pick_borda` (lines 202–229) | Scale-invariant alternative aggregation, added after peer review to correctly separate "weighted score-sum" from "Borda count" (the original docstring conflated the two — now fixed and documented in `author_response.md`). |

### 1.3 Fault injection used to prove it (not just claimed)

`src/eval.py::scenario_mesh` (see confirmed calls below) actually **kills nodes and drops packets** and still produces answers:

```
mesh.kill(k)                         # crash-fault injection (used for S3: 2/5 agents killed)
await mesh.run_rounds(n_rounds=2)    # gossip propagation under the crash/loss condition
consensus = consensus_pick(...)      # decentralized aggregation of whatever gossip arrived
replicas = await live_agents[0].node.replicate_put(...)   # R=3 replication under failure
```

This is the empirical backbone of the accuracy/latency/uptime numbers reported for S1–S6.

### 1.4 What `Mesh` (the coordinator class) is — and isn't

`Mesh` wires N `MeshNode`s together over an in-memory transport with configurable packet loss and per-link latency. Its own docstring is explicit about this: *"The transport is the only component that knows the full node set — nodes themselves only see their partial peer view, matching real P2P semantics."* In a real deployment this class is replaced by an actual network (sockets/UDP multicast/libp2p); it exists here purely to simulate physical links, not to make routing or consensus decisions. No `MeshNode` method calls back into `Mesh` for anything except message delivery and simulated latency/loss — never for a decision.

---

## 2. Does running the Kaggle notebook actually exercise the decentralization logic?

**Yes.** I checked the actual call chain, not just the notebook's stated intent:

1. Notebook cell 9 builds a real 5-agent mesh: `mesh.MeshNode(...)` + `mesh_obj.add_node(...)` wired to real HF backbones (`Gemma-2-2B-IT`, `Qwen2.5-7B-Instruct`, `Llama-3.1-8B-Instruct`) via `agents.Agent`.
2. Notebook cell 13 (`run_real()`) calls `mncd_eval.scenario_mesh(queries, n_agents=5, kill=[...], packet_loss=..., name=...)` for four of the five scenarios (S2 healthy mesh, S3 with `A3`/`A4` killed, S4 with 20% packet loss, S5 on the Karnataka APMC domain fixtures), and `mncd_eval.scenario_baseline(...)` for S1.
3. I confirmed inside `src/eval.py::scenario_mesh` that this is not a stub — it directly calls:
   - `mesh.kill(k)` — real crash-fault injection
   - `mesh.run_rounds(n_rounds=2, sleep=0.0)` — real gossip propagation
   - `agents.consensus_pick(ranks, agent_weights)` — real decentralized aggregation
   - `live_agents[0].node.replicate_put(...)` — real R=3 replication

So executing the notebook on Kaggle does not just "load the LLM backbones and run inference" — it drives the exact same gossip/replication/failure-detection/consensus code path used in the simulation results, just with real model weights instead of `MockLLM`. That is a legitimate, reviewer-defensible claim: **"the decentralization logic is exercised, not simulated separately from the LLM inference."**

One caveat worth stating up front to reviewers: `notebooks/mncd_mesh.ipynb`'s cells currently show `execution_count: null` in the repo, i.e., it has not yet been executed and its output committed. I'd recommend running it once on Kaggle GPU and committing `results_kaggle.json` (the notebook already writes this to `/kaggle/working/`) before the defense, so you can show real HF-backbone numbers side-by-side with the `MockLLM` numbers already in `metrics/results.json`, and note that a match (or a documented gap) demonstrates the mock is a faithful low-cost proxy for CI/testing.

---

## 3. Base / prior-art papers — three tiers

Reviewers will ask "what did you build on, and what's actually new?" The honest answer has three tiers, and the most important one for showing genuine novelty is the third (very recent, 2025–2026 work) — not just the classic AutoGen/MetaGPT comparison already in your related-work section.

### Tier 1 — Classical distributed-systems primitives (already cited in `mesh.py`'s own docstring)

| Paper | What MNCD takes from it |
|---|---|
| Demers et al., *Epidemic Algorithms for Replicated Database Maintenance*, PODC 1987. [ACM DL](https://dl.acm.org/doi/10.1145/41840.41841) | The push-gossip / rumor-mongering dissemination model — `_enqueue_gossip` + `_select_gossip_peers` is a direct application. |
| Eugster et al., *The Many Faces of Publish/Subscribe*, ACM Computing Surveys 35(2), 2003. | Topic-based pub/sub semantics used for `subscribe`/`publish`. |
| Van Renesse et al., *A Gossip-Style Failure Detection Service*, Middleware 1998. | Heartbeat-via-gossip failure suspicion (`absorb_heartbeats`), rather than centralized polling. |

These are 25–40 years old and universally accepted — no reviewer will contest that MNCD is *allowed* to use them; the question is what's new when applied to LLM agents (Tiers 2–3).

### Tier 2 — Centralized multi-agent LLM frameworks (the "what MNCD deliberately does NOT do")

| Framework | Documented coordination pattern | Source |
|---|---|---|
| **AutoGen** (Wu, Bansal, et al., Microsoft, 2023) | A `GroupChatManager` agent is the single point of control: *"the order of turns is maintained by a Group Chat Manager agent, which selects the next agent to speak upon receiving a message."* | [AutoGen docs](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/group-chat.html), [arXiv:2308.08155](https://arxiv.org/abs/2308.08155) |
| **MetaGPT** (Hong et al., 2023) | *"Utilizes an assembly line paradigm to assign diverse roles to various agents"* — a fixed SOP pipeline, i.e., a predetermined sequential hand-off, not a peer mesh. | [arXiv:2308.00352](https://arxiv.org/abs/2308.00352) |
| **CAMEL** (Li et al., 2023) | Role-play driven by *"inception prompting"* between a fixed pair of agents (AI User / AI Assistant) — two-party turn-taking, no gossip/replication/failure model. | [arXiv:2303.17760](https://arxiv.org/abs/2303.17760) |
| **LangGraph** (LangChain) | Explicitly documented as a *"low-level orchestration framework"*; the common multi-agent pattern is **Supervisor**, i.e., a controller agent that decomposes and routes tasks to workers. | [LangGraph docs](https://www.langchain.com/langgraph), [Supervisor vs Swarm](https://focused.io/lab/multi-agent-orchestration-in-langgraph-supervisor-vs-swarm-tradeoffs-and-architecture) |

All four have a documented single point of routing control (a manager/supervisor/fixed pipeline). If that controller dies or is slow, the whole system stalls — this is exactly the single-point-of-failure MNCD's peer mesh is designed to remove. This tier is the comparison your paper's related-work section already uses; it's necessary but not sufficient — see Tier 3.

### Tier 3 — Contemporary decentralized/gossip multi-agent LLM work (2025–2026) — the real novelty test

This is the tier that matters most for defending true novelty, because these are the papers working on the *same problem* MNCD solves, published within the last year. I read each one closely; here's exactly what each does and doesn't provide:

| Paper | Venue / Date | What it has | What it's missing (relative to MNCD) |
|---|---|---|---|
| **"A Gossip-Enhanced Communication Substrate for Agentic AI: Toward Decentralized Coordination in Large-Scale Multi-Agent Systems"** — Khan, Habiba, Khan | arXiv:2512.03285, 2 Dec 2025 | Argues gossip should be added to multi-agent stacks for decentralized, fault-tolerant knowledge diffusion. | Explicitly a **research agenda**, not an implementation: *"Rather than proposing a complete framework, this paper presents a research agenda..."* No fanout rule, no peer-selection rule, no replication, no failure detector, no consensus method, and no experiment of any kind is reported. |
| **"Consensus Is All You Need: Gossip-Based Reasoning Among Large Language Models"** — Saksham Arora | arXiv:2508.18292, 22 Aug 2025 (4 pages) | Proposes the same core idea — LLMs as peer-to-peer gossip nodes converging on a shared answer. | No protocol specification (no round structure, peer-selection, or convergence criterion), no failure model, and **no reported metrics, datasets, or baselines** — the abstract asserts "robust, resilient, and accurate" results with zero numbers behind it. |
| **AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems** — Yang et al. | arXiv:2504.00587, Apr–May 2025 | A genuinely decentralized (no central orchestrator) system: agents self-organize on a dynamic DAG and use RAG-based memory; claims fault-tolerant, privacy-preserving collaboration with higher task accuracy than centralized baselines. | Its decentralization mechanism is **graph-topology adaptation + retrieval memory**, not gossip/pub-sub. No replication factor, no heartbeat-based failure detector, and no gossip protocol are specified anywhere in the paper. |
| **Symphony: A Decentralized Multi-Agent Framework for Scalable Collective Intelligence** — Wang et al. (Gradient), 27 Aug 2025 | arXiv:2508.20019 | Concrete and evaluated: decentralized ledger of agent capabilities, Beacon-based task allocation, and an explicit weighted-majority-vote consensus formula, with real accuracy gains on BBH/AMC vs. AutoGen and CrewAI. | No gossip protocol, no pub/sub, no replication, and — critically — **no failure detector and no crash/packet-loss fault injection**. Its "fault tolerance" is really *error mitigation via multi-CoT voting on 3 always-alive agents*, not survival of actual node death or network loss. |

**The honest novelty statement this supports:** MNCD is — to the best of the searches I ran — the first system that *operationalizes* what the Dec-2025 "Gossip-Enhanced Communication Substrate" paper explicitly calls a research agenda: a concrete, integrated stack of gossip dissemination + topic pub/sub + quantified replication (R=3) + a real heartbeat-based failure detector + a weighted consensus formula, applied to LLM tool-selection/agentic tasks, and *validated under actual crash-fault and packet-loss injection* (S3: 2/5 agents killed; S4: 20% packet loss) rather than only under always-alive conditions. Symphony comes closest on the "concrete + evaluated consensus" axis but stops short of gossip/replication/failure-detection and only tests voting-based error mitigation, not agent death. AgentNet is closest on "no central orchestrator" but achieves it through DAG topology + memory rather than gossip/replication. The two 2025 gossip-for-LLM papers (Khan et al.; Arora) argue for exactly MNCD's approach but present no working system.

I'd suggest citing this framing directly in your related-work section and — separately — in your response letter to reviewers who ask "what's new here beyond AutoGen/MetaGPT/CAMEL." Note the important caveat below before finalizing that language.

**Caveat on completeness:** this is a targeted search across a handful of the most relevant recent papers, not an exhaustive systematic literature review. Given how fast this sub-area is moving (three of the four Tier-3 papers were posted in the last three months), I'd recommend one more focused search pass close to submission/defense time to catch anything published in the interim, and — if the venue allows it — running a citation search backward from the Dec-2025 "Gossip-Enhanced Communication Substrate" paper's bibliography, since it likely already surveys adjacent 2025 work systematically.

---

## 4. Suggested "what existed vs. what I added" table for your defense slide

| Component | Existed before (cite) | What MNCD adds |
|---|---|---|
| Gossip dissemination | Demers et al. 1987; "gossip-for-LLM" vision papers (Khan et al. 2025; Arora 2025) | A concrete implemented protocol (TTL=6, fanout=3, EMA-weighted peer selection) applied to LLM tool-ranking messages, not just proposed |
| Pub/sub topics | Eugster et al. 2003 | Domain-specific topic schema (`plan.candidate`, `rank.update`, `answer.final`, `__distress__`) wired directly into agent tool-selection |
| Replication for fault tolerance | Classic distributed KV replication (Demers-family) | R=3 replication measured empirically under real node kills (S3) and packet loss (S4) — not just claimed |
| Failure detection | Van Renesse et al. 1998 | Applied per-agent in an LLM mesh with quantified `failed_peers_detected` metrics and uptime/accuracy tradeoff curves |
| Decentralized consensus | Symphony's weighted-vote formula (closest prior art) | Two named, distinguished aggregation modes (weighted score-sum vs. true Borda) reconstructible by *any* peer from local gossip state, evaluated under agent failure, not just multi-CoT diversity |
| No central orchestrator | AgentNet (DAG-based); AutoGen/MetaGPT/CAMEL/LangGraph (explicitly orchestrator-based) | Same no-orchestrator property, achieved via the gossip/pub-sub/failure-detector stack rather than DAG routing, integrated with quantified fault-injection results across 6 scenarios (S1–S6) including a real agricultural domain (Karnataka APMC) |

---

*Sources consulted for Tiers 1–3 (all fetched and read directly, not from memory):*
- [Demers et al. 1987, ACM DL](https://dl.acm.org/doi/10.1145/41840.41841)
- [AutoGen arXiv:2308.08155](https://arxiv.org/abs/2308.08155) / [Group Chat docs](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/group-chat.html)
- [MetaGPT arXiv:2308.00352](https://arxiv.org/abs/2308.00352)
- [CAMEL arXiv:2303.17760](https://arxiv.org/abs/2303.17760)
- [LangGraph](https://www.langchain.com/langgraph) / [Supervisor vs Swarm](https://focused.io/lab/multi-agent-orchestration-in-langgraph-supervisor-vs-swarm-tradeoffs-and-architecture)
- [A Gossip-Enhanced Communication Substrate for Agentic AI, arXiv:2512.03285](https://arxiv.org/abs/2512.03285)
- [Consensus Is All You Need: Gossip-Based Reasoning Among LLMs, arXiv:2508.18292](https://arxiv.org/abs/2508.18292)
- [AgentNet, arXiv:2504.00587](https://arxiv.org/abs/2504.00587)
- [Symphony, arXiv:2508.20019](https://arxiv.org/html/2508.20019v1)
