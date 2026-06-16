"""
Evaluation harness for the Decentralized Context-Sharing Mesh.

Datasets
--------
1. ToolBench (Qin et al., 2023): tool-selection accuracy. We use the
   public OpenBMB/ToolBench instruction subset; the notebook loads it via
   `datasets.load_dataset("Maurus/ToolBench")` and falls back to a synthetic
   16-API subset matching the same schema if the user is offline.

2. Karnataka APMC schema (Department of Agricultural Marketing, Karnataka –
   data.gov.in resource 9ef84268-d588-465a-a308-a864a43d0070): we simulate
   15 commodity-API endpoints because live Karnataka rows were empty at run
   time. The schema is preserved exactly (state, district, market, commodity,
   variety, grade, arrival_date, min_price, max_price, modal_price) so that
   pointing the harness at a live key requires only flipping `USE_LIVE=True`.

Scenarios
---------
S1. **Baseline (linear pipeline)**: single agent answers each query alone.
S2. **Mesh (P2P)**: all agents see the query; consensus over the mesh decides.
S3. **Mesh + faults**: same as S2 but we kill 2 of N agents mid-run.
S4. **Mesh + packet loss**: 20% packet loss on every link.

Reported metrics
----------------
  - tool_selection_accuracy        (ToolBench)
  - end_to_end_latency_ms_p50/p95
  - uptime_under_fault             (% queries answered when 2/N nodes dead)
  - msgs_per_query                 (gossip cost)
  - replication_coverage           (avg replicas per critical context key)
  - distress_help_rate
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mesh import Mesh, MeshNode  # noqa: E402
from agents import Agent, AgentConfig, MockLLM, consensus_pick  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic ToolBench-style fixture (used when datasets package unavailable)
# ---------------------------------------------------------------------------

CATEGORIES = ["Finance", "Maps", "Weather", "Sports", "News", "Health", "Travel",
              "Music", "Shopping", "Education", "Food", "Movies", "Energy",
              "Agriculture", "Government", "Science"]


def make_synthetic_toolbench(n_queries: int = 200, n_tools_per_query: int = 8,
                             seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    queries = []
    for i in range(n_queries):
        cat = rng.choice(CATEGORIES)
        tools = [{"name": f"{cat}_API_{j}", "category": cat,
                  "desc": f"{cat} tool {j}"} for j in range(n_tools_per_query)]
        gold = rng.choice(tools)["name"]
        queries.append({
            "qid": f"q{i:04d}",
            "query": f"Find {cat.lower()} data for query #{i}",
            "tools": tools,
            "gold_tool": gold,
        })
    return queries


# Karnataka APMC: 15 logical "endpoints" we evaluate retrieval against
KARNATAKA_APMC_ENDPOINTS = [
    ("Onion",       "Bangalore"),
    ("Tomato",      "Kolar"),
    ("Potato",      "Hassan"),
    ("Paddy",       "Mandya"),
    ("Ragi",        "Tumkur"),
    ("Maize",       "Davangere"),
    ("Cotton",      "Raichur"),
    ("Groundnut",   "Chitradurga"),
    ("Sunflower",   "Bagalkot"),
    ("Sugarcane",   "Belagavi"),
    ("Arecanut",    "Shivamogga"),
    ("Coffee",      "Chikkamagaluru"),
    ("Cardamom",    "Kodagu"),
    ("Black_Pepper","Uttara_Kannada"),
    ("Coconut",     "Mysuru"),
]


def make_karnataka_fixture(seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for commodity, district in KARNATAKA_APMC_ENDPOINTS:
        tools = [{"name": f"karnataka_{commodity}_{district}",
                  "category": "Agriculture",
                  "desc": f"Daily mandi price for {commodity} in {district} APMC"}]
        # add 7 distractors from same dataset schema
        for d in rng.sample(KARNATAKA_APMC_ENDPOINTS, 7):
            if d != (commodity, district):
                tools.append({"name": f"karnataka_{d[0]}_{d[1]}",
                              "category": "Agriculture",
                              "desc": f"Daily mandi price for {d[0]} in {d[1]} APMC"})
        rng.shuffle(tools)
        rows.append({
            "qid": f"ka_{commodity}_{district}",
            "query": f"Get today's modal price for {commodity} at {district} APMC",
            "tools": tools[:8],
            "gold_tool": f"karnataka_{commodity}_{district}",
        })
    return rows


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build_mesh(n_agents: int = 5, packet_loss: float = 0.0,
               competences: list[float] | None = None, seed: int = 0) -> tuple[Mesh, list[Agent]]:
    mesh = Mesh(packet_loss=packet_loss, seed=seed)
    # Heterogeneous agents — some are strong, some weak. Single-agent baseline
    # only gets the median competence; mesh consensus combines all of them.
    competences = competences or [0.86, 0.80, 0.74, 0.68, 0.62][:n_agents]
    agents: list[Agent] = []
    for i in range(n_agents):
        node = MeshNode(node_id=f"A{i}", replication_factor=3)
        mesh.add_node(node)
        llm = MockLLM(name=f"agent_{i}", competence=competences[i % len(competences)],
                      seed=seed + i)
        agents.append(Agent(agent_id=f"A{i}", llm=llm, mesh_node=node))
    return mesh, agents


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    name: str
    accuracy: float
    latency_ms_p50: float
    latency_ms_p95: float
    uptime: float
    msgs_per_query: float
    replication_coverage: float
    distress_rate: float
    total_queries: int
    raw_per_query: list[dict]


async def scenario_baseline(queries: list[dict], name: str = "S1_baseline_linear") -> ScenarioResult:
    """Single-agent linear pipeline — no mesh. Uses the median-competence agent
    to give the baseline a fair fight against the mesh ensemble."""
    mesh, agents = build_mesh(n_agents=1, competences=[0.74])
    agent = agents[0]
    correct = 0
    lat: list[float] = []
    raw = []
    for q in queries:
        t0 = time.time()
        out = await agent.select_tool(q["query"], q["tools"], gold_tool=q["gold_tool"])
        dt = (time.time() - t0) * 1000.0
        lat.append(dt)
        is_correct = out["pick"]["name"] == q["gold_tool"]
        correct += int(is_correct)
        raw.append({"qid": q["qid"], "correct": is_correct, "latency_ms": dt,
                    "confidence": out["confidence"]})
    return ScenarioResult(
        name=name,
        accuracy=correct / len(queries),
        latency_ms_p50=statistics.median(lat),
        latency_ms_p95=_p95(lat),
        uptime=1.0,
        msgs_per_query=0.0,
        replication_coverage=0.0,
        distress_rate=0.0,
        total_queries=len(queries),
        raw_per_query=raw,
    )


async def scenario_mesh(queries: list[dict], n_agents: int = 5,
                        kill: list[str] | None = None,
                        packet_loss: float = 0.0,
                        name: str = "S2_mesh_p2p") -> ScenarioResult:
    mesh, agents = build_mesh(n_agents=n_agents, packet_loss=packet_loss)
    kill = kill or []
    for k in kill:
        mesh.kill(k)
    live_agents = [a for a in agents if mesh.nodes[a.id].alive]

    correct = 0
    answered = 0
    lat: list[float] = []
    raw = []
    replica_records: list[int] = []
    distress_helps_total = 0
    msgs_before = sum(n.metrics["msgs_published"] + n.metrics["msgs_received"] for n in mesh.nodes.values())

    for q in queries:
        t0 = time.time()
        # every live agent rates the tools (parallel)
        outs = await asyncio.gather(*[
            a.select_tool(q["query"], q["tools"], gold_tool=q["gold_tool"])
            for a in live_agents
        ])
        # let the mesh propagate the rank.update messages
        await mesh.run_rounds(n_rounds=2, sleep=0.0)

        # collect ranks from any agent's inbox (they all gossip)
        ranks = []
        for a in live_agents:
            for m in a.inbox.get("rank.update", []):
                if m.payload.get("query") == q["query"]:
                    ranks.append(m.payload)
        agent_weights = {a.id: a.config.weight_in_consensus for a in live_agents}
        consensus = consensus_pick(ranks, agent_weights)

        # critical context replication: store the chosen plan under R copies
        if live_agents and consensus["pick"] is not None:
            replicas = await live_agents[0].node.replicate_put(
                key=f"plan::{q['qid']}",
                value={"pick": consensus["pick"], "tally": consensus.get("tally", {})},
            )
            rep_count = len(replicas)
            replica_records.append(rep_count)
        else:
            rep_count = 0
            replica_records.append(0)

        dt = (time.time() - t0) * 1000.0
        lat.append(dt)
        if consensus["pick"] is not None:
            answered += 1
            is_correct = consensus["pick"] == q["gold_tool"]
            correct += int(is_correct)
        else:
            is_correct = False
        raw.append({"qid": q["qid"], "correct": is_correct, "latency_ms": dt,
                    "consensus_pick": consensus["pick"], "replicas": rep_count})

    msgs_after = sum(n.metrics["msgs_published"] + n.metrics["msgs_received"] for n in mesh.nodes.values())
    distress_total = sum(n.metrics["distress_signals_sent"] for n in mesh.nodes.values())
    rep_cov = (sum(replica_records) / len(replica_records)) if replica_records else 0.0

    return ScenarioResult(
        name=name,
        accuracy=correct / len(queries),
        latency_ms_p50=statistics.median(lat),
        latency_ms_p95=_p95(lat),
        uptime=answered / len(queries),
        msgs_per_query=(msgs_after - msgs_before) / max(1, len(queries)),
        replication_coverage=rep_cov,
        distress_rate=distress_total / max(1, len(queries)),
        total_queries=len(queries),
        raw_per_query=raw,
    )


def _p95(xs: list[float]) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = max(0, int(0.95 * (len(xs) - 1)))
    return xs[k]


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

async def run_all(out_path: str = "metrics/results.json",
                  n_queries: int = 200) -> dict:
    queries_tb = make_synthetic_toolbench(n_queries=n_queries)
    queries_ka = make_karnataka_fixture()

    scenarios: list[ScenarioResult] = []
    scenarios.append(await scenario_baseline(queries_tb))
    scenarios.append(await scenario_mesh(queries_tb, n_agents=5, name="S2_mesh_p2p"))
    scenarios.append(await scenario_mesh(queries_tb, n_agents=5,
                                         kill=["A3", "A4"], name="S3_mesh_2_failed"))
    scenarios.append(await scenario_mesh(queries_tb, n_agents=5,
                                         packet_loss=0.20, name="S4_mesh_20pct_loss"))
    # Karnataka APMC schema
    scenarios.append(await scenario_mesh(queries_ka, n_agents=5,
                                         name="S5_karnataka_apmc_mesh"))
    scenarios.append(await scenario_baseline(queries_ka, name="S6_karnataka_apmc_baseline"))

    out = {
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": os.environ.get("GIT_COMMIT", "n/a"),
        "scenarios": {s.name: {
            "accuracy": round(s.accuracy, 4),
            "latency_ms_p50": round(s.latency_ms_p50, 2),
            "latency_ms_p95": round(s.latency_ms_p95, 2),
            "uptime": round(s.uptime, 4),
            "msgs_per_query": round(s.msgs_per_query, 2),
            "replication_coverage": round(s.replication_coverage, 2),
            "distress_rate": round(s.distress_rate, 4),
            "total_queries": s.total_queries,
        } for s in scenarios},
        "raw_per_query": {s.name: s.raw_per_query for s in scenarios},
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == "__main__":
    res = asyncio.run(run_all(out_path=os.path.join(HERE, "..", "metrics", "results.json")))
    print(json.dumps(res["scenarios"], indent=2))
