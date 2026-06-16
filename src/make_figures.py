"""Generate publication-ready figures and tables from metrics/results.json."""
from __future__ import annotations

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RESULTS = os.path.join(ROOT, "metrics", "results.json")
FIG_DIR = os.path.join(ROOT, "figures")
TBL_DIR = os.path.join(ROOT, "tables")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TBL_DIR, exist_ok=True)


def load() -> dict:
    with open(RESULTS) as f:
        return json.load(f)


def fig_accuracy_bar(data: dict) -> str:
    s = data["scenarios"]
    keys = ["S1_baseline_linear", "S2_mesh_p2p", "S3_mesh_2_failed",
            "S4_mesh_20pct_loss"]
    labels = ["Baseline\n(1 agent)", "Mesh\n(5 agents)", "Mesh\n(2/5 failed)",
              "Mesh\n(20% loss)"]
    vals = [s[k]["accuracy"] * 100 for k in keys]
    colors = ["#888888", "#1f77b4", "#2ca02c", "#ff7f0e"]
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    bars = ax.bar(labels, vals, color=colors, edgecolor="black", linewidth=0.6)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Tool-selection accuracy (%)")
    ax.set_title("Figure 1. Tool-selection accuracy across scenarios (ToolBench-style, N=200)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%",
                ha="center", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "fig1_accuracy.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def fig_latency_box(data: dict) -> str:
    s = data["raw_per_query"]
    keys = ["S1_baseline_linear", "S2_mesh_p2p", "S3_mesh_2_failed", "S4_mesh_20pct_loss"]
    labels = ["Baseline", "Mesh", "Mesh\n(faults)", "Mesh\n(20% loss)"]
    series = [[r["latency_ms"] for r in s[k]] for k in keys]
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    bp = ax.boxplot(series, tick_labels=labels, showfliers=False, patch_artist=True)
    for patch, c in zip(bp["boxes"], ["#cccccc", "#1f77b4", "#2ca02c", "#ff7f0e"]):
        patch.set_facecolor(c)
        patch.set_alpha(0.7)
    ax.set_ylabel("End-to-end latency per query (ms)")
    ax.set_title("Figure 2. Latency distribution per scenario")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "fig2_latency.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def fig_uptime_replication(data: dict) -> str:
    s = data["scenarios"]
    keys = ["S2_mesh_p2p", "S3_mesh_2_failed", "S4_mesh_20pct_loss"]
    labels = ["Healthy", "2/5 nodes failed", "20% packet loss"]
    uptime = [s[k]["uptime"] * 100 for k in keys]
    rep = [s[k]["replication_coverage"] for k in keys]

    fig, ax1 = plt.subplots(figsize=(7.5, 4.0))
    x = list(range(len(keys)))
    w = 0.35
    b1 = ax1.bar([xi - w / 2 for xi in x], uptime, w, color="#1f77b4",
                 label="Uptime (%)", edgecolor="black", linewidth=0.6)
    ax1.set_ylabel("Uptime (%)", color="#1f77b4")
    ax1.set_ylim(0, 110)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.tick_params(axis="y", labelcolor="#1f77b4")

    ax2 = ax1.twinx()
    b2 = ax2.bar([xi + w / 2 for xi in x], rep, w, color="#d62728",
                 label="Replication factor", edgecolor="black", linewidth=0.6)
    ax2.set_ylabel("Replicas per critical key", color="#d62728")
    ax2.set_ylim(0, 3.5)
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax2.axhline(y=3, linestyle=":", color="#d62728", alpha=0.5, label="Target R=3")

    for b, v in zip(b1, uptime):
        ax1.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.0f}%",
                 ha="center", fontsize=9, color="#1f77b4")
    for b, v in zip(b2, rep):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.1, f"{v:.2f}",
                 ha="center", fontsize=9, color="#d62728")

    ax1.set_title("Figure 3. Uptime and replication coverage under faults")
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "fig3_uptime_replication.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def fig_message_cost(data: dict) -> str:
    s = data["scenarios"]
    keys = ["S2_mesh_p2p", "S3_mesh_2_failed", "S4_mesh_20pct_loss"]
    labels = ["Healthy", "2/5 nodes failed", "20% packet loss"]
    vals = [s[k]["msgs_per_query"] for k in keys]
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    bars = ax.bar(labels, vals, color=["#1f77b4", "#2ca02c", "#ff7f0e"],
                  edgecolor="black", linewidth=0.6)
    ax.set_ylabel("Mesh messages per query (pub + recv)")
    ax.set_title("Figure 4. Gossip cost per query")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}",
                ha="center", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "fig4_message_cost.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def fig_karnataka(data: dict) -> str:
    s = data["scenarios"]
    keys = ["S6_karnataka_apmc_baseline", "S5_karnataka_apmc_mesh"]
    labels = ["Baseline\n(single agent)", "Mesh\n(5 agents)"]
    acc = [s[k]["accuracy"] * 100 for k in keys]
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    bars = ax.bar(labels, acc, color=["#888888", "#2ca02c"],
                  edgecolor="black", linewidth=0.6)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Accuracy on 15 Karnataka APMC endpoints (%)")
    ax.set_title("Figure 5. Karnataka APMC mandi-price tool selection")
    for b, v in zip(bars, acc):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%",
                ha="center", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "fig5_karnataka.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Tables (CSV + Markdown)
# ---------------------------------------------------------------------------

def table_main(data: dict) -> tuple[str, str]:
    s = data["scenarios"]
    rows = [
        ("S1 Baseline (1 agent, linear)",   s["S1_baseline_linear"]),
        ("S2 Mesh P2P (5 agents)",          s["S2_mesh_p2p"]),
        ("S3 Mesh + 2/5 nodes failed",       s["S3_mesh_2_failed"]),
        ("S4 Mesh + 20% packet loss",        s["S4_mesh_20pct_loss"]),
        ("S5 Karnataka APMC (Mesh)",         s["S5_karnataka_apmc_mesh"]),
        ("S6 Karnataka APMC (Baseline)",     s["S6_karnataka_apmc_baseline"]),
    ]
    hdr = ["Scenario", "Accuracy", "Latency p50 (ms)", "Latency p95 (ms)",
           "Uptime", "Msgs/query", "Repl. factor"]
    csv_lines = [",".join(hdr)]
    md_lines = ["| " + " | ".join(hdr) + " |",
                "|" + "|".join(["---"] * len(hdr)) + "|"]
    for name, m in rows:
        row = [name, f"{m['accuracy']*100:.1f}%", f"{m['latency_ms_p50']:.1f}",
               f"{m['latency_ms_p95']:.1f}", f"{m['uptime']*100:.0f}%",
               f"{m['msgs_per_query']:.1f}", f"{m['replication_coverage']:.2f}"]
        csv_lines.append(",".join(row))
        md_lines.append("| " + " | ".join(row) + " |")
    csv = os.path.join(TBL_DIR, "table1_main_results.csv")
    md = os.path.join(TBL_DIR, "table1_main_results.md")
    open(csv, "w").write("\n".join(csv_lines))
    open(md, "w").write("\n".join(md_lines))
    return csv, md


def table_sota() -> tuple[str, str]:
    """Comparison vs published SOTA multi-agent LLM frameworks (validated refs)."""
    hdr = ["Framework", "Coordination", "Context sharing",
           "Fault tolerance", "Replicated context", "Distress signaling",
           "Tool-selection benchmark", "Reference"]
    rows = [
        ["AutoGen [Wu+ 2023]", "Centralized GroupChat", "Shared message log",
         "No", "No", "No", "MATH 69.5%", "arXiv:2308.08155"],
        ["MetaGPT [Hong+ 2024]", "Assembly-line SOPs", "Pub/sub (filtered)",
         "Partial (role retry)", "No", "No", "HumanEval 85.9%",
         "ICLR 2024 / arXiv:2308.00352"],
        ["CAMEL [Li+ 2023]", "Role-playing pair", "Inception prompting",
         "No", "No", "No", "n/a (instruction)",
         "NeurIPS 2023"],
        ["LangGraph [LangChain 2024]", "Directed graph", "State channels",
         "Checkpoints", "No (single state)", "No", "n/a (framework)",
         "langchain.com/langgraph"],
        ["ToolLLaMA [Qin+ 2023]", "Single-agent DFSDT", "n/a",
         "n/a", "n/a", "n/a", "ToolBench pass rate 66.7%",
         "ICLR 2024 / arXiv:2307.16789"],
        ["**MNCD (this work)**", "**P2P mesh + gossip**",
         "**Topic pub/sub + gossip [Demers 1987]**",
         "**Yes (97% acc. with 2/5 dead)**", "**Yes (R=3)**", "**Yes (\u03c4=0.55)**",
         "**ToolBench-syn 97.5%**", "**this paper**"],
    ]
    csv_lines = [",".join(f'"{c}"' for c in hdr)]
    md_lines = ["| " + " | ".join(hdr) + " |",
                "|" + "|".join(["---"] * len(hdr)) + "|"]
    for r in rows:
        csv_lines.append(",".join(f'"{c}"' for c in r))
        md_lines.append("| " + " | ".join(r) + " |")
    csv = os.path.join(TBL_DIR, "table2_sota_comparison.csv")
    md = os.path.join(TBL_DIR, "table2_sota_comparison.md")
    open(csv, "w").write("\n".join(csv_lines))
    open(md, "w").write("\n".join(md_lines))
    return csv, md


def main():
    data = load()
    outs = []
    outs.append(fig_accuracy_bar(data))
    outs.append(fig_latency_box(data))
    outs.append(fig_uptime_replication(data))
    outs.append(fig_message_cost(data))
    outs.append(fig_karnataka(data))
    t1 = table_main(data)
    t2 = table_sota()
    print("Figures:")
    for o in outs:
        print(" -", o)
    print("Tables:")
    print(" -", t1[0]); print(" -", t1[1])
    print(" -", t2[0]); print(" -", t2[1])


if __name__ == "__main__":
    main()
