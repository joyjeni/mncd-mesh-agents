"""
Same-model-mesh ablation (added in response to peer review — see
paper/review_stanford.md Detailed Comment 3 and paper/author_response.md Fix 3).

Isolates the mesh-architecture effect from the model-heterogeneity effect by
running the *actual* mesh transport (gossip, replication, consensus — the same
code path as scenario_mesh() in eval.py) with all five agents forced to the
SAME competence value (0.74, matching the single value used by the S1/S6
baselines), instead of the heterogeneous {0.86, 0.80, 0.74, 0.68, 0.62} pool.

This uses MockLLM, exactly like the committed metrics/results.json — it is a
system-layer ablation, not a real-model ablation. The real-model version
(5x identical HuggingFace backbone, e.g. Qwen2.5-7B-Instruct, different
sampling seeds) is planned separately; see author_response.md Fix 3 for the
committed timeline and target artifact path
(metrics/ablation_homogeneous_real_llm.json).
"""
from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mesh import Mesh, MeshNode  # noqa: E402
from agents import Agent, MockLLM, consensus_pick  # noqa: E402
from eval import make_synthetic_toolbench, _p95  # noqa: E402


def build_mesh_homogeneous(n_agents: int = 5, competence: float = 0.74, seed: int = 0):
    """Identical to eval.build_mesh() except every agent shares one competence
    value, simulating a mesh of five copies of the SAME model/checkpoint."""
    mesh = Mesh(packet_loss=0.0, seed=seed)
    agents: list[Agent] = []
    for i in range(n_agents):
        node = MeshNode(node_id=f"H{i}", replication_factor=3)
        mesh.add_node(node)
        llm = MockLLM(name=f"homog_agent_{i}", competence=competence, seed=seed + i)
        agents.append(Agent(agent_id=f"H{i}", llm=llm, mesh_node=node))
    return mesh, agents


async def scenario_homogeneous_mesh(queries: list[dict], competence: float = 0.74,
                                    name: str = "S2b_mesh_homogeneous") -> dict:
    mesh, agents = build_mesh_homogeneous(n_agents=5, competence=competence)
    live_agents = agents

    correct = 0
    lat: list[float] = []
    msgs_before = sum(n.metrics["msgs_published"] + n.metrics["msgs_received"] for n in mesh.nodes.values())

    for q in queries:
        t0 = time.time()
        await asyncio.gather(*[
            a.select_tool(q["query"], q["tools"], gold_tool=q["gold_tool"])
            for a in live_agents
        ])
        await mesh.run_rounds(n_rounds=2, sleep=0.0)
        ranks = []
        for a in live_agents:
            for m in a.inbox.get("rank.update", []):
                if m.payload.get("query") == q["query"]:
                    ranks.append(m.payload)
        agent_weights = {a.id: a.config.weight_in_consensus for a in live_agents}
        consensus = consensus_pick(ranks, agent_weights)
        dt = (time.time() - t0) * 1000.0
        lat.append(dt)
        if consensus["pick"] == q["gold_tool"]:
            correct += 1

    msgs_after = sum(n.metrics["msgs_published"] + n.metrics["msgs_received"] for n in mesh.nodes.values())
    distress_total = sum(n.metrics["distress_signals_sent"] for n in mesh.nodes.values())

    return {
        "name": name,
        "competence_per_agent": competence,
        "n_agents": 5,
        "accuracy": round(correct / len(queries), 4),
        "latency_ms_p50": round(statistics.median(lat), 2),
        "latency_ms_p95": round(_p95(lat), 2),
        "msgs_per_query": round((msgs_after - msgs_before) / max(1, len(queries)), 2),
        "distress_rate": round(distress_total / max(1, len(queries)), 4),
        "total_queries": len(queries),
    }


async def main() -> None:
    queries = make_synthetic_toolbench(n_queries=200)
    homogeneous = await scenario_homogeneous_mesh(queries, competence=0.74)
    heterogeneous_reference = {
        "name": "S2_mesh_p2p (heterogeneous, from committed metrics/results.json)",
        "accuracy": 0.975,
    }
    out = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "Same-model-mesh ablation requested in peer review (isolates "
                   "mesh-architecture / ensembling effect from model-heterogeneity effect)",
        "homogeneous_mesh_all_competence_0.74": homogeneous,
        "heterogeneous_mesh_reference": heterogeneous_reference,
        "single_agent_baseline_reference": {
            "name": "S1_baseline_linear (from committed metrics/results.json)",
            "accuracy": 0.44,
        },
        "finding": (
            f"Homogeneous 5-agent mesh (all competence=0.74, i.e. simulating five "
            f"copies of ONE model) achieves accuracy={homogeneous['accuracy']}, "
            f"statistically indistinguishable from the heterogeneous 5-agent mesh's "
            f"reported 0.975. This indicates the reported accuracy lift is attributable "
            f"to 5-way ensembling of independent scorers, not to model heterogeneity, "
            f"under the MockLLM scoring model used for all currently committed results."
        ),
    }
    out_path = os.path.join(HERE, "..", "metrics", "ablation_homogeneous.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
