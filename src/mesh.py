"""
Decentralized Context Sharing Mesh for Multi-Agent LLM Systems
==============================================================
A peer-to-peer mesh network for LLM agent coordination with:
  - Topic-based publish/subscribe (Eugster et al., 2003)
  - Gossip / epidemic update propagation (Demers et al., 1987)
  - Replication factor R for critical context (default R=3)
  - Failure detection via heartbeat gossip (Van Renesse et al., 1998)
  - Adaptive edge weights via exponential moving average of peer utility
  - Distress signaling: low-confidence outputs trigger help-request broadcast

This module implements the *system layer* (network, replication, failure handling)
independent of the LLM backbone. The LLM-bound agents wrap this layer in
agents.py and the ToolBench / Karnataka APMC evaluation runs in eval.py.

References
----------
[Demers1987]  Demers, A. et al. (1987). Epidemic Algorithms for Replicated
              Database Maintenance. PODC '87.
[Eugster2003] Eugster, P.T. et al. (2003). The Many Faces of Publish/Subscribe.
              ACM Computing Surveys, 35(2).
[VanRenesse1998] Van Renesse, R. et al. (1998). A Gossip-Style Failure
              Detection Service. Middleware '98.
[Kempe2004]   Kempe, D. et al. (2004). Spatial gossip and resource location
              protocols. J. ACM 51(6).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional


# ---------------------------------------------------------------------------
# Core data types
# ---------------------------------------------------------------------------

@dataclass
class ContextMessage:
    """A single context update broadcast on the mesh."""
    msg_id: str
    topic: str
    payload: dict
    origin: str               # agent id that produced it
    timestamp: float
    ttl: int = 6              # max hops (log2(N) is enough at N<=64)
    seen_by: set[str] = field(default_factory=set)
    confidence: float = 1.0   # producer-reported confidence in [0,1]
    is_distress: bool = False # set when confidence < tau_distress

    def fingerprint(self) -> str:
        """Stable id used for de-duplication during gossip."""
        h = hashlib.sha1(f"{self.origin}|{self.topic}|{self.timestamp}".encode()).hexdigest()
        return h[:16]


@dataclass
class PeerStats:
    """EMA-tracked per-peer performance for adaptive edge weighting."""
    success: float = 1.0      # smoothed prob(useful response)
    latency_ms: float = 50.0  # smoothed RTT
    last_seen: float = 0.0
    weight: float = 1.0       # selection probability weight

    def update(self, success: bool, latency_ms: float, alpha: float = 0.3) -> None:
        self.success = (1 - alpha) * self.success + alpha * (1.0 if success else 0.0)
        self.latency_ms = (1 - alpha) * self.latency_ms + alpha * latency_ms
        self.last_seen = time.time()
        # weight rewards high success and low latency
        self.weight = max(1e-3, self.success / (1.0 + self.latency_ms / 1000.0))


# ---------------------------------------------------------------------------
# Mesh node
# ---------------------------------------------------------------------------

class MeshNode:
    """A single peer in the decentralized context-sharing mesh.

    The node maintains:
      * an in-memory pub/sub bus with topic subscriptions
      * a partial view of peers + per-peer EMA statistics
      * a deduplicated rumor cache (recently seen msg_ids)
      * a replicated key/value store for critical context (R copies)
      * a failure detector based on gossip heartbeats

    Public coroutines:
      publish, subscribe, gossip_round, request_help, replicate_put, replicate_get
    """

    HEARTBEAT_INTERVAL = 1.0      # seconds
    FAILURE_TIMEOUT = 4.0         # seconds without heartbeat -> suspect
    RUMOR_CACHE_SIZE = 4096
    DEFAULT_FANOUT = 3            # gossip targets per round (≈ log fanout)

    def __init__(self, node_id: str, replication_factor: int = 3,
                 distress_threshold: float = 0.55):
        self.node_id = node_id
        self.R = replication_factor
        self.tau_distress = distress_threshold

        self.peers: dict[str, PeerStats] = {}
        self.subscriptions: dict[str, list[Callable[[ContextMessage], Awaitable[None]]]] = defaultdict(list)
        self.seen: deque[str] = deque(maxlen=self.RUMOR_CACHE_SIZE)
        self.seen_set: set[str] = set()

        # replicated store: key -> {value, replicas:set[node_id], version}
        self.kv: dict[str, dict] = {}

        # gossip outbox per peer
        self.outbox: dict[str, list[ContextMessage]] = defaultdict(list)

        # failure detector
        self.suspected: set[str] = set()

        # injected at runtime by Mesh
        self._mesh: Optional["Mesh"] = None
        self.alive: bool = True

        # internal metrics
        self.metrics = {
            "msgs_published": 0,
            "msgs_received": 0,
            "msgs_dropped_seen": 0,
            "msgs_dropped_ttl": 0,
            "distress_signals_sent": 0,
            "distress_signals_received": 0,
            "replicate_writes": 0,
            "replicate_reads": 0,
            "failed_peers_detected": 0,
        }

    # --- pub/sub ----------------------------------------------------------

    def subscribe(self, topic: str, handler: Callable[[ContextMessage], Awaitable[None]]) -> None:
        self.subscriptions[topic].append(handler)

    async def publish(self, topic: str, payload: dict, confidence: float = 1.0) -> ContextMessage:
        msg = ContextMessage(
            msg_id="",
            topic=topic,
            payload=payload,
            origin=self.node_id,
            timestamp=time.time(),
            confidence=confidence,
            is_distress=(confidence < self.tau_distress),
        )
        msg.msg_id = msg.fingerprint()
        msg.seen_by.add(self.node_id)
        self.metrics["msgs_published"] += 1
        if msg.is_distress:
            self.metrics["distress_signals_sent"] += 1
        await self._deliver_local(msg)
        self._enqueue_gossip(msg)
        return msg

    async def _deliver_local(self, msg: ContextMessage) -> None:
        for handler in self.subscriptions.get(msg.topic, []):
            try:
                await handler(msg)
            except Exception:  # noqa: BLE001
                # subscriber errors must never break the mesh
                continue
        if msg.is_distress:
            for handler in self.subscriptions.get("__distress__", []):
                try:
                    await handler(msg)
                except Exception:  # noqa: BLE001
                    continue

    # --- gossip -----------------------------------------------------------

    def _enqueue_gossip(self, msg: ContextMessage) -> None:
        if msg.ttl <= 0:
            return
        # mark seen locally to short-circuit echoes
        if msg.msg_id not in self.seen_set:
            self.seen.append(msg.msg_id)
            self.seen_set.add(msg.msg_id)
            if len(self.seen) == self.seen.maxlen:
                # rotate set
                self.seen_set = set(self.seen)
        # pick fanout peers weighted by adaptive weight, excluding suspected
        targets = self._select_gossip_peers()
        for p in targets:
            self.outbox[p].append(msg)

    def _select_gossip_peers(self, fanout: int = DEFAULT_FANOUT) -> list[str]:
        candidates = [p for p in self.peers if p not in self.suspected and p != self.node_id]
        if not candidates:
            return []
        weights = [self.peers[p].weight for p in candidates]
        k = min(fanout, len(candidates))
        # weighted sampling w/o replacement
        chosen: list[str] = []
        cand = list(candidates)
        w = list(weights)
        for _ in range(k):
            total = sum(w)
            if total <= 0:
                idx = random.randrange(len(cand))
            else:
                r = random.random() * total
                acc = 0.0
                idx = 0
                for i, wi in enumerate(w):
                    acc += wi
                    if r <= acc:
                        idx = i
                        break
            chosen.append(cand.pop(idx))
            w.pop(idx)
        return chosen

    async def gossip_round(self) -> None:
        """One round of push-gossip; called by Mesh scheduler."""
        if not self.alive:
            return
        # flush outbox via mesh transport
        for peer, msgs in list(self.outbox.items()):
            if not msgs:
                continue
            for msg in msgs:
                t0 = time.time()
                ok = await self._mesh.transport(self.node_id, peer, msg)
                rtt = (time.time() - t0) * 1000.0
                stats = self.peers.setdefault(peer, PeerStats())
                stats.update(success=ok, latency_ms=rtt)
            self.outbox[peer].clear()

    async def receive(self, msg: ContextMessage) -> bool:
        """Called by Mesh when a peer transports a message to us."""
        if not self.alive:
            return False
        self.metrics["msgs_received"] += 1
        if msg.msg_id in self.seen_set:
            self.metrics["msgs_dropped_seen"] += 1
            return True  # ack-but-ignore
        if msg.ttl <= 0:
            self.metrics["msgs_dropped_ttl"] += 1
            return True
        msg.ttl -= 1
        msg.seen_by.add(self.node_id)
        if msg.is_distress:
            self.metrics["distress_signals_received"] += 1
        await self._deliver_local(msg)
        # re-broadcast (rumor mongering with TTL decrement)
        self._enqueue_gossip(msg)
        return True

    # --- replication ------------------------------------------------------

    async def replicate_put(self, key: str, value: Any) -> list[str]:
        """Store key under R copies (self + R-1 peers selected by weight)."""
        self.metrics["replicate_writes"] += 1
        version = time.time()
        self.kv[key] = {"value": value, "version": version, "replicas": {self.node_id}}
        replicas: set[str] = {self.node_id}
        peers = self._select_gossip_peers(fanout=self.R - 1)
        for p in peers:
            ok = await self._mesh.replicate_call(self.node_id, p, key, value, version)
            if ok:
                replicas.add(p)
        self.kv[key]["replicas"] = replicas
        return sorted(replicas)

    async def replicate_get(self, key: str) -> Optional[Any]:
        """Read key; on local miss, query replicas via the mesh."""
        self.metrics["replicate_reads"] += 1
        if key in self.kv:
            return self.kv[key]["value"]
        # ask any peer
        for p in self._select_gossip_peers(fanout=self.R):
            v = await self._mesh.replicate_lookup(self.node_id, p, key)
            if v is not None:
                self.kv[key] = {"value": v, "version": time.time(), "replicas": {self.node_id, p}}
                return v
        return None

    def replicate_accept(self, key: str, value: Any, version: float) -> bool:
        """Called by Mesh when a peer asks us to hold a replica."""
        if not self.alive:
            return False
        cur = self.kv.get(key)
        if cur is None or cur["version"] < version:
            self.kv[key] = {"value": value, "version": version,
                            "replicas": (cur["replicas"] if cur else set()) | {self.node_id}}
        return True

    # --- failure detector -------------------------------------------------

    def heartbeat_tick(self) -> dict[str, float]:
        """Return our heartbeat timestamps for peers (gossiped via mesh)."""
        return {self.node_id: time.time()}

    def absorb_heartbeats(self, hb: dict[str, float]) -> None:
        now = time.time()
        for pid, ts in hb.items():
            if pid == self.node_id:
                continue
            stats = self.peers.setdefault(pid, PeerStats())
            stats.last_seen = max(stats.last_seen, ts)
        # mark stale peers as suspected
        for pid, stats in self.peers.items():
            if now - stats.last_seen > self.FAILURE_TIMEOUT and pid not in self.suspected:
                self.suspected.add(pid)
                self.metrics["failed_peers_detected"] += 1

    # --- distress ---------------------------------------------------------

    async def request_help(self, query: str, context: dict) -> None:
        """Emit a high-priority distress broadcast for low-confidence outputs."""
        await self.publish(
            topic="__distress__",
            payload={"query": query, "context": context, "requester": self.node_id},
            confidence=0.0,  # forces is_distress=True
        )


# ---------------------------------------------------------------------------
# Mesh transport (in-memory; pluggable for real network later)
# ---------------------------------------------------------------------------

class Mesh:
    """Coordinator that wires N MeshNodes together over an in-memory transport
    with configurable packet-loss and per-link latency. The transport is the
    only component that knows the full node set — nodes themselves only see
    their partial peer view, matching real P2P semantics."""

    def __init__(self, packet_loss: float = 0.0, link_latency_ms: tuple[int, int] = (1, 5),
                 seed: int = 42):
        self.nodes: dict[str, MeshNode] = {}
        self.packet_loss = packet_loss
        self.link_latency_ms = link_latency_ms
        random.seed(seed)

    def add_node(self, node: MeshNode) -> None:
        node._mesh = self
        self.nodes[node.node_id] = node
        # bootstrap: every node knows every other node (partial views possible later)
        for other_id, other in self.nodes.items():
            if other_id == node.node_id:
                continue
            node.peers.setdefault(other_id, PeerStats(last_seen=time.time()))
            other.peers.setdefault(node.node_id, PeerStats(last_seen=time.time()))

    def kill(self, node_id: str) -> None:
        """Simulate a node crash."""
        if node_id in self.nodes:
            self.nodes[node_id].alive = False

    def revive(self, node_id: str) -> None:
        if node_id in self.nodes:
            self.nodes[node_id].alive = True

    async def _link_delay(self) -> None:
        lo, hi = self.link_latency_ms
        await asyncio.sleep(random.uniform(lo, hi) / 1000.0)

    async def transport(self, src: str, dst: str, msg: ContextMessage) -> bool:
        if random.random() < self.packet_loss:
            return False
        await self._link_delay()
        node = self.nodes.get(dst)
        if node is None or not node.alive:
            return False
        return await node.receive(msg)

    async def replicate_call(self, src: str, dst: str, key: str, value: Any, version: float) -> bool:
        if random.random() < self.packet_loss:
            return False
        await self._link_delay()
        node = self.nodes.get(dst)
        if node is None or not node.alive:
            return False
        return node.replicate_accept(key, value, version)

    async def replicate_lookup(self, src: str, dst: str, key: str) -> Optional[Any]:
        if random.random() < self.packet_loss:
            return None
        await self._link_delay()
        node = self.nodes.get(dst)
        if node is None or not node.alive:
            return None
        rec = node.kv.get(key)
        return rec["value"] if rec else None

    async def run_rounds(self, n_rounds: int = 20, sleep: float = 0.05) -> None:
        for _ in range(n_rounds):
            # gossip heartbeats
            global_hb: dict[str, float] = {}
            for nid, node in self.nodes.items():
                if node.alive:
                    global_hb.update(node.heartbeat_tick())
            for node in self.nodes.values():
                if node.alive:
                    node.absorb_heartbeats(global_hb)
            # run gossip rounds in parallel
            await asyncio.gather(*[n.gossip_round() for n in self.nodes.values() if n.alive])
            await asyncio.sleep(sleep)

    def aggregate_metrics(self) -> dict:
        agg: dict[str, Any] = {"per_node": {}, "totals": defaultdict(int)}
        for nid, node in self.nodes.items():
            agg["per_node"][nid] = dict(node.metrics)
            agg["per_node"][nid]["alive"] = node.alive
            agg["per_node"][nid]["suspected"] = sorted(node.suspected)
            agg["per_node"][nid]["kv_keys"] = len(node.kv)
            for k, v in node.metrics.items():
                agg["totals"][k] += v
        agg["totals"] = dict(agg["totals"])
        agg["live_fraction"] = sum(1 for n in self.nodes.values() if n.alive) / max(1, len(self.nodes))
        return agg
