"""Generate a side-by-side architecture comparison diagram:
SOTA multi-agent LLM frameworks (AutoGen, MetaGPT, CAMEL, LangGraph,
ToolLLaMA) vs. MNCD (this work).

Saved under /diagrams so it is version-controlled in git, and referenced
from paper/mncd_paper.tex as Figure fig:sota-arch.
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

NODE_FACE = "#d9d9d9"
NODE_EDGE = "#333333"
MNCD_FACE = "#cfe2f3"
MNCD_EDGE = "#1c4587"


def _node(ax, x, y, r=0.30, face=NODE_FACE, edge=NODE_EDGE, lw=1.1, label=None,
          fontsize=7.5):
    circ = patches.Circle((x, y), r, facecolor=face, edgecolor=edge, linewidth=lw,
                           zorder=3)
    ax.add_patch(circ)
    if label:
        ax.text(x, y, label, ha="center", va="center", fontsize=fontsize,
                fontweight="bold", zorder=4)
    return (x, y)


def _panel_frame(ax, x0, y0, w, h, title, subtitle, highlight=False):
    face = "#eaf1fb" if highlight else "#fafafa"
    edge = MNCD_EDGE if highlight else "#999999"
    lw = 2.0 if highlight else 1.0
    box = patches.FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.06",
                                  facecolor=face, edgecolor=edge, linewidth=lw,
                                  zorder=1)
    ax.add_patch(box)
    ax.text(x0 + w / 2, y0 + h - 0.28, title, ha="center", fontsize=10.5,
            fontweight="bold", color=(MNCD_EDGE if highlight else "#222"))
    ax.text(x0 + w / 2, y0 + 0.20, subtitle, ha="center", fontsize=8.2,
            color="#444", style="italic")


def panel_autogen(ax, x0, y0, w, h):
    _panel_frame(ax, x0, y0, w, h, "AutoGen", "Centralized GroupChat")
    cx, cy = x0 + w / 2, y0 + h / 2 + 0.15
    hub = _node(ax, cx, cy, r=0.24, face="#f4cccc", label="Mgr", fontsize=6.5)
    leaves = [(cx - 0.85, cy - 0.55), (cx - 0.30, cy - 0.75),
              (cx + 0.30, cy - 0.75), (cx + 0.85, cy - 0.55)]
    for i, (lx, ly) in enumerate(leaves):
        ax.plot([cx, lx], [cy, ly], "-", color="#888", lw=1.0, zorder=2)
        _node(ax, lx, ly, r=0.20, label=f"A{i}", fontsize=6.5)


def panel_metagpt(ax, x0, y0, w, h):
    _panel_frame(ax, x0, y0, w, h, "MetaGPT", "SOP assembly line")
    cy = y0 + h / 2 + 0.15
    margin = 0.38
    span = w - 2 * margin
    labels = ["PM", "Arch", "Eng", "QA"]
    xs = [x0 + margin + i * (span / (len(labels) - 1)) for i in range(len(labels))]
    for i, x in enumerate(xs):
        if i > 0:
            ax.annotate("", xy=(x - 0.19, cy), xytext=(xs[i - 1] + 0.19, cy),
                        arrowprops=dict(arrowstyle="->", lw=1.1, color="#888"),
                        zorder=2)
    for i, x in enumerate(xs):
        _node(ax, x, cy, r=0.18, label=labels[i], fontsize=5.6)


def panel_camel(ax, x0, y0, w, h):
    _panel_frame(ax, x0, y0, w, h, "CAMEL", "Role-playing pair")
    cy = y0 + h / 2 + 0.15
    x1, x2 = x0 + w / 2 - 0.60, x0 + w / 2 + 0.60
    ax.annotate("", xy=(x2 - 0.30, cy + 0.16), xytext=(x1 + 0.30, cy + 0.16),
                arrowprops=dict(arrowstyle="->", lw=1.1, color="#888"), zorder=2)
    ax.annotate("", xy=(x1 + 0.30, cy - 0.16), xytext=(x2 - 0.30, cy - 0.16),
                arrowprops=dict(arrowstyle="->", lw=1.1, color="#888"), zorder=2)
    _node(ax, x1, cy, r=0.26, label="User", fontsize=6.5)
    _node(ax, x2, cy, r=0.26, label="Asst", fontsize=6.5)


def panel_langgraph(ax, x0, y0, w, h):
    _panel_frame(ax, x0, y0, w, h, "LangGraph", "Directed graph, single state")
    cy = y0 + h / 2 + 0.15
    n1 = (x0 + 0.45, cy + 0.35)
    n2 = (x0 + 0.45, cy - 0.35)
    n3 = (x0 + w / 2 + 0.15, cy)
    n4 = (x0 + w - 0.45, cy)
    _node(ax, *n1, r=0.20, label="S1", fontsize=6.2)
    _node(ax, *n2, r=0.20, label="S2", fontsize=6.2)
    _node(ax, *n3, r=0.20, label="S3", fontsize=6.2)
    _node(ax, *n4, r=0.20, label="S4", fontsize=6.2)
    for a, b in [(n1, n3), (n2, n3), (n3, n4)]:
        ax.annotate("", xy=(b[0] - 0.20, b[1]), xytext=(a[0] + 0.20, a[1]),
                    arrowprops=dict(arrowstyle="->", lw=1.1, color="#888"), zorder=2)


def panel_toolllama(ax, x0, y0, w, h):
    _panel_frame(ax, x0, y0, w, h, "ToolLLaMA", "Single-agent DFSDT")
    cx, cy = x0 + w / 2, y0 + h / 2 - 0.05
    _node(ax, cx, cy, r=0.30, face="#fff2cc", label="Agent", fontsize=7.0)
    ax.annotate("", xy=(cx + 0.32, cy + 0.28), xytext=(cx + 0.68, cy + 0.55),
                arrowprops=dict(arrowstyle="<->", lw=1.0, color="#888"), zorder=2)
    ax.text(cx + 0.78, cy + 0.60, "search\ntree", fontsize=6.2, ha="center",
            va="center", color="#555")


def panel_mncd(ax, x0, y0, w, h):
    _panel_frame(ax, x0, y0, w, h, "MNCD (this work)",
                 "P2P mesh, gossip diffusion, R=3 replication, distress channel (τ=0.55)",
                 highlight=True)
    cx, cy, r = x0 + w / 2, y0 + h / 2 + 0.10, 0.62
    names = ["A0\nPlan", "A1\nRetr", "A2\nExec", "A3\nVerify", "A4\nSpec"]
    coords = []
    for i in range(5):
        ang = math.pi / 2 + i * 2 * math.pi / 5
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang) * 0.85
        coords.append((x, y))
    for i in range(5):
        for j in range(i + 1, 5):
            x1, y1 = coords[i]
            x2, y2 = coords[j]
            ax.plot([x1, x2], [y1, y2], "-", color=MNCD_EDGE, alpha=0.35, lw=1.0,
                     zorder=2)
    for (x, y), name in zip(coords, names):
        _node(ax, x, y, r=0.27, face=MNCD_FACE, edge=MNCD_EDGE, lw=1.4,
              label=name, fontsize=6.0)


def diagram_sota_comparison():
    fig, ax = plt.subplots(figsize=(12, 7.4))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 7.4)
    ax.axis("off")

    ax.text(6.3, 7.05,
            "Figure C. Architectural Comparison — SOTA Frameworks vs. MNCD (This Work)",
            ha="center", fontsize=13.5, fontweight="bold")

    # Row of 5 small SOTA panels
    panel_w, panel_h = 2.15, 2.15
    gap = 0.18
    total_w = 5 * panel_w + 4 * gap
    x_start = (12.6 - total_w) / 2
    y_top = 6.55 - panel_h

    panels = [panel_autogen, panel_metagpt, panel_camel, panel_langgraph,
              panel_toolllama]
    for i, fn in enumerate(panels):
        x0 = x_start + i * (panel_w + gap)
        fn(ax, x0, y_top, panel_w, panel_h)

    # Large MNCD panel below, spanning full width
    mncd_h = 2.85
    mncd_y0 = 0.35
    panel_mncd(ax, 1.1, mncd_y0, 10.4, mncd_h)

    # Connective arrow + label between rows
    arrow_top = y_top - 0.10
    arrow_bot = mncd_y0 + mncd_h + 0.10
    ax.annotate("", xy=(6.3, arrow_bot), xytext=(6.3, arrow_top),
                arrowprops=dict(arrowstyle="-|>", lw=1.6, color="#555"))
    ax.text(6.65, (arrow_top + arrow_bot) / 2,
            "decentralize: no single\npoint of failure",
            fontsize=8.5, color="#555", va="center")

    fig.tight_layout()
    png = os.path.join(OUT, "sota_comparison_architectures.png")
    svg = os.path.join(OUT, "sota_comparison_architectures.svg")
    fig.savefig(png, dpi=220)
    fig.savefig(svg)
    plt.close(fig)
    return png, svg


if __name__ == "__main__":
    p, s = diagram_sota_comparison()
    print("SOTA comparison diagram:", p)
    print("SOTA comparison diagram:", s)
