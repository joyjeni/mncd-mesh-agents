"""
LLM-bound agents that sit on top of the MeshNode transport.

Each agent owns:
  * a MeshNode (P2P transport, pub/sub, replication, failure detection)
  * an LLM backbone (loaded from HuggingFace; mocked here so the mesh code
    is testable in CPU-only sandboxes — the Kaggle notebook swaps in the
    real models)
  * a small set of skills (tool-selection, planning, retrieval, execution)

The mesh is intentionally backbone-agnostic. The notebook (notebooks/mncd_mesh.ipynb)
mounts Gemma-2-2B-IT, Qwen2.5-7B-Instruct, and Llama-3.1-8B-Instruct.

The shared *context bus* exposes the following well-known topics:
  - "plan.candidate"   : a proposed plan for the current query
  - "tool.evidence"    : observations / API results from tool calls
  - "rank.update"      : updated tool-selection rankings
  - "answer.partial"   : partial answers from any agent
  - "answer.final"     : final answer (consensus)
  - "__distress__"     : low-confidence help request (system topic)
"""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from mesh import ContextMessage, MeshNode


# ---------------------------------------------------------------------------
# LLM backbone abstraction
# ---------------------------------------------------------------------------

class LLMBackbone:
    """Minimal interface implemented by both the mock and the real HF models."""
    name: str = "mock"

    async def generate(self, prompt: str, max_new_tokens: int = 256, **kwargs) -> str:
        raise NotImplementedError

    async def score_tool(self, query: str, tools: list[dict]) -> list[float]:
        raise NotImplementedError


class MockLLM(LLMBackbone):
    """CPU-only stand-in used by unit tests and the evaluation harness when GPU is absent.

    The mock is deterministic given a seed and is parameterised by a per-agent
    `competence` so we can simulate heterogeneous agents (this matches the
    real fine-tuned variants — e.g. a math-focused agent vs. an API-focused one).
    """
    def __init__(self, name: str, competence: float = 0.85, seed: int = 0):
        self.name = name
        self.competence = competence
        self.rng = random.Random(seed)

    async def generate(self, prompt: str, max_new_tokens: int = 256, **kwargs) -> str:
        await asyncio.sleep(0.01)
        return f"[{self.name}] {prompt[:60]}..."

    async def score_tool(self, query: str, tools: list[dict]) -> list[float]:
        await asyncio.sleep(0.005)
        # competence-weighted scoring; gold tool gets a boost if competence is high
        scores: list[float] = []
        gold_idx = next((i for i, t in enumerate(tools) if t.get("is_gold")), None)
        for i, _ in enumerate(tools):
            base = self.rng.uniform(0.0, 1.0)
            if i == gold_idx:
                base = base * (1 - self.competence) + self.competence
            scores.append(base)
        return scores


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

@dataclass
class AgentConfig:
    role: str = "generalist"        # e.g. planner, retriever, executor, verifier
    subscribes: tuple[str, ...] = ("plan.candidate", "tool.evidence", "rank.update",
                                   "answer.partial")
    publishes: tuple[str, ...] = ("plan.candidate", "tool.evidence", "rank.update",
                                  "answer.partial", "answer.final")
    confidence_floor: float = 0.55  # below this -> distress
    weight_in_consensus: float = 1.0


class Agent:
    """An LLM-bound peer in the mesh."""

    def __init__(self, agent_id: str, llm: LLMBackbone, mesh_node: MeshNode,
                 config: Optional[AgentConfig] = None):
        self.id = agent_id
        self.llm = llm
        self.node = mesh_node
        self.config = config or AgentConfig()
        # local memory of incoming context, indexed by topic
        self.inbox: dict[str, list[ContextMessage]] = {t: [] for t in self.config.subscribes}
        # subscribe to system topic
        self.node.subscribe("__distress__", self._on_distress)
        for t in self.config.subscribes:
            self.node.subscribe(t, self._on_topic(t))
        self.metrics = {
            "tool_calls": 0,
            "tool_correct": 0,
            "answers_emitted": 0,
            "distress_helps": 0,
            "latency_ms_sum": 0.0,
        }

    def _on_topic(self, topic: str) -> Callable:
        async def handler(msg: ContextMessage) -> None:
            self.inbox.setdefault(topic, []).append(msg)
        return handler

    async def _on_distress(self, msg: ContextMessage) -> None:
        # only respond if the request did not originate from us
        if msg.payload.get("requester") == self.id:
            return
        await self.handle_distress(msg)

    # ------------------------------------------------------------------
    # public coroutines used by the runner
    # ------------------------------------------------------------------

    async def select_tool(self, query: str, tools: list[dict], gold_tool: Optional[str] = None) -> dict:
        """Score candidate tools, broadcast the ranking, and return the top pick."""
        t0 = time.time()
        scored_tools = [dict(t, is_gold=(t["name"] == gold_tool)) for t in tools] if gold_tool else tools
        scores = await self.llm.score_tool(query, scored_tools)
        top_idx = max(range(len(tools)), key=lambda i: scores[i])
        pick = tools[top_idx]
        confidence = float(scores[top_idx])

        if gold_tool is not None:
            self.metrics["tool_correct"] += int(pick["name"] == gold_tool)
        self.metrics["tool_calls"] += 1
        self.metrics["latency_ms_sum"] += (time.time() - t0) * 1000.0

        await self.node.publish(
            topic="rank.update",
            payload={"query": query, "ranking": sorted(zip([t["name"] for t in tools], scores),
                                                       key=lambda x: -x[1]),
                     "pick": pick["name"], "confidence": confidence, "agent": self.id},
            confidence=confidence,
        )
        if confidence < self.config.confidence_floor:
            await self.node.request_help(query=query, context={"tools": [t["name"] for t in tools]})
        return {"pick": pick, "confidence": confidence}

    async def handle_distress(self, msg: ContextMessage) -> None:
        """Provide a second opinion on a peer's low-confidence query."""
        self.metrics["distress_helps"] += 1
        # in real code we'd re-score; for the mock we publish our best guess
        tools = msg.payload.get("context", {}).get("tools", [])
        if not tools:
            return
        # publish a help message; consumers can break ties with this
        await self.node.publish(
            topic="answer.partial",
            payload={"helper": self.id, "for": msg.payload.get("requester"),
                     "vote": tools[0], "via": "distress"},
            confidence=0.75,
        )


# ---------------------------------------------------------------------------
# Consensus over the mesh
# ---------------------------------------------------------------------------

def consensus_pick(ranks: list[dict], agent_weights: dict[str, float]) -> dict:
    """Borda-style weighted vote across all rank.update messages on the bus."""
    score: dict[str, float] = {}
    for r in ranks:
        agent_id = r.get("agent", "?")
        w = agent_weights.get(agent_id, 1.0)
        for tool_name, s in r.get("ranking", []):
            score[tool_name] = score.get(tool_name, 0.0) + w * float(s)
    if not score:
        return {"pick": None, "score": 0.0}
    best = max(score.items(), key=lambda kv: kv[1])
    return {"pick": best[0], "score": best[1], "tally": dict(sorted(score.items(),
                                                                    key=lambda kv: -kv[1]))}
