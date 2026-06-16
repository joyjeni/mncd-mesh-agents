"""Generate architecture and algorithm diagrams as PNG + SVG.

Saved under /diagrams so they are version-controlled in git.
"""
from __future__ import annotations

import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "diagrams")
os.makedirs(OUT, exist_ok=True)


def diagram_architecture():
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")

    title = "Figure A. Decentralized Context-Sharing Mesh — System Architecture"
    ax.text(6, 8.6, title, ha="center", fontsize=14, fontweight="bold")

    # Five agent nodes on a pentagon
    cx, cy, r = 6, 4.5, 2.8
    agent_names = ["A0 Planner", "A1 Retriever", "A2 Executor",
                   "A3 Verifier", "A4 Specialist"]
    coords = []
    for i in range(5):
        ang = math.pi / 2 + i * 2 * math.pi / 5
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang)
        coords.append((x, y))

    # Edges (fully connected mesh)
    for i in range(5):
        for j in range(i + 1, 5):
            x1, y1 = coords[i]
            x2, y2 = coords[j]
            ax.plot([x1, x2], [y1, y2], "-", color="#888888", alpha=0.35, linewidth=1.0)

    # Nodes
    for (x, y), name in zip(coords, agent_names):
        box = patches.FancyBboxPatch((x - 0.85, y - 0.4), 1.7, 0.8,
                                     boxstyle="round,pad=0.08",
                                     edgecolor="black",
                                     facecolor="#cfe2f3", linewidth=1.2)
        ax.add_patch(box)
        ax.text(x, y + 0.08, name, ha="center", fontsize=10, fontweight="bold")
        ax.text(x, y - 0.22, "LLM + MeshNode", ha="center", fontsize=8, color="#444")

    # Components ring around each node — just annotate one
    legend_x, legend_y = 0.4, 7.5
    legend_items = [
        ("Pub/Sub bus",        "#cfe2f3"),
        ("Gossip outbox",      "#d9ead3"),
        ("Replicated K/V (R=3)","#fff2cc"),
        ("Failure detector",   "#f4cccc"),
        ("Distress channel",   "#ead1dc"),
    ]
    for i, (lab, c) in enumerate(legend_items):
        y = legend_y - i * 0.45
        ax.add_patch(patches.FancyBboxPatch((legend_x, y - 0.15), 0.5, 0.3,
                                            boxstyle="round,pad=0.02",
                                            facecolor=c, edgecolor="black", linewidth=0.8))
        ax.text(legend_x + 0.6, y, lab, fontsize=10, va="center")
    ax.text(legend_x, legend_y + 0.55, "MeshNode internals",
            fontsize=11, fontweight="bold")

    # External I/O
    box1 = patches.FancyBboxPatch((9.0, 7.3), 2.6, 1.1, boxstyle="round,pad=0.08",
                                  facecolor="#f9cb9c", edgecolor="black", linewidth=1.0)
    ax.add_patch(box1)
    ax.text(10.3, 8.05, "Query in", ha="center", fontsize=10, fontweight="bold")
    ax.text(10.3, 7.7, "ToolBench / Karnataka", ha="center", fontsize=9)
    ax.text(10.3, 7.45, "APMC schema", ha="center", fontsize=9)
    ax.annotate("", xy=(coords[0][0] + 0.9, coords[0][1] + 0.4),
                xytext=(9.2, 7.5),
                arrowprops=dict(arrowstyle="->", lw=1.4, color="#666"))

    box2 = patches.FancyBboxPatch((9.0, 0.6), 2.6, 1.1, boxstyle="round,pad=0.08",
                                  facecolor="#b6d7a8", edgecolor="black", linewidth=1.0)
    ax.add_patch(box2)
    ax.text(10.3, 1.35, "Consensus answer", ha="center", fontsize=10, fontweight="bold")
    ax.text(10.3, 1.0, "Weighted vote across", ha="center", fontsize=9)
    ax.text(10.3, 0.75, "all rank.update msgs", ha="center", fontsize=9)
    ax.annotate("", xy=(9.2, 1.5),
                xytext=(coords[2][0] + 0.9, coords[2][1] - 0.4),
                arrowprops=dict(arrowstyle="->", lw=1.4, color="#666"))

    # Topics legend
    topics_box = patches.FancyBboxPatch((0.4, 0.5), 3.2, 3.2, boxstyle="round,pad=0.1",
                                        facecolor="#ffffff", edgecolor="#666",
                                        linewidth=1.0)
    ax.add_patch(topics_box)
    ax.text(2.0, 3.4, "Topics (pub/sub)", fontsize=11, fontweight="bold", ha="center")
    topics = ["plan.candidate", "tool.evidence", "rank.update",
              "answer.partial", "answer.final", "__distress__ (system)"]
    for i, t in enumerate(topics):
        ax.text(0.6, 2.95 - i * 0.4, "• " + t, fontsize=10)

    # Caption
    ax.text(6, 0.15,
            "All agents are equal peers. Updates propagate via push gossip with TTL = 6; "
            "critical context is replicated R = 3.",
            ha="center", fontsize=9, style="italic", color="#444")

    fig.tight_layout()
    png = os.path.join(OUT, "architecture.png")
    svg = os.path.join(OUT, "architecture.svg")
    fig.savefig(png, dpi=200)
    fig.savefig(svg)
    plt.close(fig)
    return png, svg


def diagram_algorithm():
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 11)
    ax.axis("off")

    ax.text(6, 10.5,
            "Figure B. Algorithm Walkthrough — Query → Consensus Answer",
            ha="center", fontsize=14, fontweight="bold")

    steps = [
        ("1. Query enters via any peer A0",
         "Topic-tagged message msg = (qid, query, tools[])",
         "#cfe2f3"),
        ("2. A0 publishes on topic 'plan.candidate'",
         "Local subscribers fire; outbox queues for fanout=3 peers",
         "#cfe2f3"),
        ("3. Gossip round (push)",
         "Each peer relays via weighted sampling: w_p = success_p / (1 + lat_p/1s)",
         "#d9ead3"),
        ("4. All live peers score tools in parallel",
         "score_tool(query, tools[]) → ranking, confidence",
         "#fff2cc"),
        ("5. Each peer publishes 'rank.update'",
         "if confidence < τ (=0.55) → emit '__distress__' broadcast",
         "#ead1dc"),
        ("6. Distress responders broadcast a second opinion",
         "Helpers add weight to under-represented votes",
         "#ead1dc"),
        ("7. Consensus pick",
         "argmax over Σ_agents w_a · score_a(tool); replicated R=3 to K/V",
         "#f4cccc"),
        ("8. Failure detector tick (every round)",
         "If last_seen(p) > 4s → suspect(p); future fanout skips p",
         "#fce5cd"),
        ("9. Answer emitted on 'answer.final'",
         "Stored under key plan::qid across 3 replicas — survives 2 failures",
         "#b6d7a8"),
    ]
    y0 = 9.5
    h = 0.85
    for i, (title, sub, color) in enumerate(steps):
        y = y0 - i * (h + 0.12)
        box = patches.FancyBboxPatch((0.7, y - h / 2), 10.6, h,
                                     boxstyle="round,pad=0.08",
                                     facecolor=color, edgecolor="black", linewidth=0.9)
        ax.add_patch(box)
        ax.text(1.0, y + 0.18, title, fontsize=10.5, fontweight="bold", va="center")
        ax.text(1.0, y - 0.18, sub, fontsize=9.5, va="center", color="#222")
        if i < len(steps) - 1:
            ax.annotate("", xy=(6, y - h / 2 - 0.02),
                        xytext=(6, y - h / 2 + 0.10),
                        arrowprops=dict(arrowstyle="->", lw=1.2, color="#333"))

    fig.tight_layout()
    png = os.path.join(OUT, "algorithm_walkthrough.png")
    svg = os.path.join(OUT, "algorithm_walkthrough.svg")
    fig.savefig(png, dpi=200)
    fig.savefig(svg)
    plt.close(fig)
    return png, svg


if __name__ == "__main__":
    a = diagram_architecture()
    b = diagram_algorithm()
    print("Architecture:", a)
    print("Algorithm:   ", b)
