# Author Response to Reviewers

**Manuscript:** MNCD: Mesh Network Context Diffusion — Fault-Tolerant Multi-Agent Coordination via Pub/Sub, Gossip, Replication, and Distress Signaling
**Repository:** `mncd-mesh-agents`
**Response Date:** Revision Round 1
**Reviews addressed:** `paper/review_stanford.md` (Distributed Systems), `paper/review_cmu.md` (Agent Orchestration / Empirical Benchmarking), plus the external PhD examiner's report

We thank both reviewers and the examiner for their thorough, independent engagement with the manuscript and repository. Both reviews reached materially convergent conclusions from different expertise angles, and — in the case of the distributed-systems review — independently re-executed the repository's own code rather than relying on static reading, which surfaced a finding (the distress channel's 0.0000 trigger rate across every reported scenario) that we had not caught ourselves. We address every concern below, organized by reviewer/examiner and by concern, indicating precisely what has already been changed in the repository (with file/line references), what new experiment we commit to running with a concrete artifact path and timeline, and — in the small number of cases where we believe a finding overstates a problem — a reasoned pushback grounded in repository evidence rather than assertion.

---

## Response to the Examiner's Report (three original concerns)

---

### Examiner-1: Table 2's SOTA comparison mixes unrelated benchmarks

**Concern:** AutoGen's 69.5% (MATH), MetaGPT's 85.9% (HumanEval), and ToolLLaMA's 66.7% (real ToolBench) are placed in the same numeric column as MNCD's 97.5% (its own synthetic benchmark) — three different tasks and datasets.

**Status: Fixed.**

Both independent reviews reached the same conclusion (`review_stanford.md` Detailed Comment 1; `review_cmu.md` Detailed Comment 3), and we agree without reservation. We have:

1. Created `tables/table2_qualitative.md`, which drops the numeric "Tool-selection benchmark" column entirely and retains only the qualitative axes that are already accurately sourced per-framework (coordination style, context sharing, fault tolerance, replication, distress/escalation, consensus mechanism, reference). This supersedes `tables/table2_sota_comparison.md` and `.csv`, which are retained in the repository only as a labeled-superseded historical artifact, not as the paper's Table 2.
2. Note for the LaTeX paper itself: on re-reading `paper/mncd_paper.tex` line-by-line (lines 285–304, `\begin{table*}[t]...\label{tab:sota}`), the submitted paper's actual Table 2 was **already qualitative** — six columns (Coord., Context sharing, Fault tol., Replication, Distress, Reference), with no numeric benchmark column at all. The numeric-mixing problem exists only in the repository's separate dashboard artifacts (`tables/table2_sota_comparison.md/.csv`, which feed the Vercel dashboard), not in the LaTeX manuscript that would be defended. We flag this distinction explicitly so the committee is not misled by a mismatch between the paper PDF and the public repository: **the dashboard/repo table has now been corrected to match the paper's own (already-correct) qualitative structure**, rather than the paper needing to be changed to match the repo.
3. We additionally commit to the real-baseline path recommended by both reviewers as a stronger, secondary fix: implementing AutoGen's GroupChat (lowest-effort real comparator, actively maintained pip package) re-run on MNCD's own 200-query synthetic fixture, targeting `tables/table2_same_benchmark.csv`. **Timeline:** 3 weeks from this response (implementation + one seed sweep); tracked as an open experiment, not yet started.

---

### Examiner-2: Single-agent baseline's tool access is unspecified

**Concern:** Does S1 get the same tool/API access as mesh agents, or is it memory-only?

**Status: Fixed (clarification) + Rebutted (in part).**

We have added the following explicit "Baseline Specification" language, corroborated by direct code inspection (`src/eval.py::scenario_baseline`, `src/eval.py::build_mesh`):

> S1 (and S6) use exactly the same `Agent.select_tool()` code path, the same 8-candidate-tool list per query, and the same `MockLLM.score_tool()` scoring function as any individual mesh agent. The baseline is not deprived of tools, retries, or candidate context relative to a single mesh agent — it is a single instance of the identical scoring mechanism used inside the mesh, run alone instead of in a 5-way ensemble.

This has been added to `README.md`'s Results section (see the "Important caveat" block) and will be added as a dedicated subsection in `paper/mncd_paper.tex` §IV (Evaluation → Setup) in the next LaTeX revision pass.

**Partial rebuttal:** the examiner's concern, read narrowly ("is tool access unspecified/asymmetric"), is not borne out by the code — access is symmetric, confirmed by both independent reviewers reading the same functions (`review_stanford.md` Detailed Comment 2 explicitly states "the baseline is *not* artificially weakened in the sense of API access"). However, we do not read this as good news for the paper, and we are not using the symmetry to defend the headline claim: **the symmetry is precisely why the entire 44%→97.5% delta is attributable to ensembling five identical-mechanism scorers, not to any distinguishing architectural capability** — see our response to Reviewer 1 (R1-W1) below, which we treat as the more serious version of this concern.

---

### Examiner-3: Model heterogeneity is a confound not isolated from the architectural contribution

**Concern:** Gemma-2-2B/Qwen2.5-7B/Llama-3.1-8B heterogeneity is a confound; an ablation with all five agents on the same model would isolate the architectural contribution from the ensembling effect.

**Status: Fixed (system-layer ablation, run and committed) + Planned (real-model ablation).**

See our detailed response to Reviewer 1's R1-W3/R1-C3 and Reviewer 2's Focus Area 5 below — we have already implemented, executed, and committed the same-model-mesh ablation at the system layer, and it returns essentially the same accuracy as the heterogeneous mesh, confirming the examiner's suspicion. A real-model version of this ablation is planned with a concrete artifact path and timeline (see below).

---

## Response to Reviewer 1 (Stanford — Distributed Systems)

---

### R1-W1 / R1-C2 / R1-C3: The accuracy gain is explainable as ensemble averaging, not mesh architecture; no ablation isolates the two effects

**Reviewer concern:** "I re-implemented and independently re-ran the repository's exact scoring function outside of any mesh/gossip/replication code path... and obtained ~98.8% accuracy... Both figures match the reported 97.5% mesh accuracy within noise... the entire lift is ensemble size, not model diversity, and quite possibly not 'mesh architecture' either."

**Authors' response:** The reviewer is correct, and this is the single most important finding in either review. We reproduced the reviewer's result independently using the repository's actual production code path (not a re-implementation) rather than a standalone simulation:

1. **We added `src/ablation_homogeneous.py`**, which runs the real `scenario_mesh`-equivalent code path (`Mesh`, `MeshNode`, gossip rounds via `mesh.run_rounds()`, `consensus_pick()` — the identical machinery used to produce the committed S2 result) with all five agents forced to competence=0.74 (the same value used for the S1/S6 baseline), i.e., a mesh of five copies of one "model."
2. **Result, committed to `metrics/ablation_homogeneous.json`:** the homogeneous mesh achieves **97.5% accuracy**, statistically indistinguishable from the heterogeneous mesh's reported 97.5%, and far above the single-agent 44.0% baseline. This confirms, using the actual gossip/replication/consensus code (not a bypass), that model heterogeneity contributes nothing measurable to the reported accuracy lift under the current `MockLLM` evaluation.
3. We revise the abstract and README framing accordingly (see README "Results" section, "Important caveat" block, and the corrected Novel Contribution wording): the claim is narrowed from "the mesh architecture doubles accuracy" to **"aggregating five independent scorers via the mesh's consensus mechanism doubles accuracy under the current mock evaluation; this reflects a well-known ensembling effect and does not yet establish that gossip, replication, or distress signaling individually contribute to task accuracy — their contribution is to delivering that ensembling result under partial failure, not to the accuracy figure itself."**
4. **Planned real-model ablation (not yet run):** we commit to re-running this same homogeneous-vs-heterogeneous comparison with the real HuggingFace backbones — specifically 5× `Qwen2.5-7B-Instruct` (different sampling seeds/temperatures, temperature ∈ {0.3, 0.5, 0.7, 0.9, 1.1}) as the homogeneous condition, vs. the paper's stated Gemma-2-2B/Qwen2.5-7B/Llama-3.1-8B mix as the heterogeneous condition, on a 200-query real ToolBench subset (see R1-W4/R2-Focus-1 below for the dataset). **Target artifact:** `metrics/ablation_homogeneous_real_llm.json`. **Timeline:** 5 weeks (blocked on GPU/Kaggle access — see Reproducibility fix below), reported as a committed follow-up, not yet started.

---

### R1-W2: The distress channel has a measured 0.0000 trigger rate in every reported scenario

**Reviewer concern:** "distress_rate = 0.0000 in all six scenarios... The distress mechanism is therefore architecturally present but empirically inert in every number the paper reports."

**Authors' response:** Confirmed and accepted in full; this is a finding we had not identified ourselves prior to review, and we thank the reviewer for re-executing the code directly rather than relying on the committed JSON alone.

1. **Root cause confirmed by our own re-execution:** `MockLLM.score_tool()` reports the *winning* score among several near-uniform random draws as "confidence" (`src/agents.py`, `Agent.select_tool`, `confidence = float(scores[top_idx])`). The maximum of several uniform draws is a maximum-order-statistic that is rarely below τ=0.55, regardless of whether the winning pick is correct — so the distress gate essentially never fires under this scoring model.
2. **README correction (already made):** the Distress Trigger section of `README.md` now states explicitly, in a "Correction (post-peer-review)" block, that the measured trigger rate is 0.0000 across all six scenarios, and removes the previously unimplemented "escalates to R=5" claim (see R1-C4 below).
3. **Planned fix:** we commit to two changes before the next results refresh: (a) redesigning the confidence signal so it reflects calibration quality rather than raw winning-score magnitude (e.g., margin between top-1 and top-2 scores, which is far more likely to fall below τ for genuinely ambiguous queries); (b) adding a dedicated adversarial low-confidence fixture (queries with two near-identical-quality candidate tools) specifically designed to exercise the distress path at a non-trivial rate. **Target artifact:** `metrics/results_distress_stress_test.json`. **Timeline:** 4 weeks, not yet started.

---

### R1-W3: Table 2 mixes four incompatible benchmarks

**Status:** See Examiner-1 response above — fixed via `tables/table2_qualitative.md`, with the additional clarification that the LaTeX paper's own Table 2 was already qualitative and did not require this fix; only the repository's separate dashboard table did.

---

### R1-W4: No `requirements.txt` or pinned dependency file exists

**Reviewer concern:** "No `requirements.txt`, `environment.yml`, or pinned dependency file exists anywhere in the repository, despite the README instructing `pip install -r requirements.txt`."

**Status: Fixed.** We have added `requirements.txt` at the repository root, pinning `transformers==4.44.2`, `torch==2.4.0`, `accelerate==0.33.0`, `bitsandbytes==0.43.3`, `datasets==2.21.0`, `huggingface_hub==0.24.6`, `sentencepiece==0.2.0`, `numpy==1.26.4` for the real-backbone notebook path, and documenting that the core evaluation harness (`src/mesh.py`, `src/agents.py`, `src/eval.py`) has zero third-party dependencies (standard library only), which the file now states explicitly at the top.

---

### R1-C4: README's claimed "R=5 escalation on distress" has no corresponding code; gossip fanout claim is asserted, not fitted to data

**Reviewer concern:** "`self.R` is fixed at construction and never mutated... this is either an aspirational claim that was never implemented or a description of a planned-but-abandoned feature."

**Authors' response:** The reviewer is correct on both counts.

1. **README correction (already made):** the "increases replication factor to R=5" claim has been removed from `README.md`'s Distress Trigger section and replaced with an accurate description (`Agent.handle_distress()` re-routes to a backup agent set for a second opinion; no R escalation occurs) plus an explicit note documenting the removal and why.
2. **Gossip fanout fitting:** we accept this is asserted rather than measured. We commit to fitting the empirical message-cost curve (msgs/query at N ∈ {5, 10, 20, 40}, see R2 Focus Area 5 below) against the theoretical \(O(Nk\log N)\) model and reporting a goodness-of-fit statistic (R²) in the revised paper's Cost Analysis subsection. **Timeline:** bundled with the scalability experiment below, 4 weeks.

---

### R1-C6: Karnataka scenario is confirmed synthetic despite framing implying live validation

**Status: Fixed.** `README.md`'s "Data Sources" section now leads with an explicit "S5/S6 are synthetic, not live queries (corrected post-peer-review)" statement, rather than disclosing this only in the paper's Limitations section. We will add the equivalent statement to `paper/mncd_paper.tex` §IV-A (Setup) in the next LaTeX pass, immediately after the sentence introducing the Karnataka scenario, rather than deferring it to §VI (Limitations).

---

### R1-W5 (novelty scoping)

**Status: Fixed.** `README.md`'s "Novel Contribution" heading now reads "first system to combine all four of the following specifically for LLM agent meshes" with an inline citation to the paper's own Related Work section acknowledging that pub/sub, gossip, replication, and confidence-gated escalation are individually decades-old primitives. We separately note (and do not consider this fully resolved) that this narrower claim's evidentiary support for the distress-signaling component specifically remains weak given R1-W2 above — narrowing the *wording* does not by itself resolve the *evidence* gap, which is why R1-W2's stress-test experiment remains open.

---

## Response to Reviewer 2 (CMU — Agent Orchestration / Empirical Benchmarking)

---

### R2 Focus Area 1: Benchmark construct validity — "ToolBench-syn" is not a faithful proxy for real ToolBench

**Reviewer concern:** "A single-shot 8-way pick among near-arbitrary template strings is intrinsically a much easier classification problem than real ToolBench's retrieval-and-execution task... this is sufficient on its own to explain the entire ~31-point gap."

**Authors' response:** We accept this fully and do not dispute the reviewer's construct-validity analysis.

1. **Planned experiment:** we commit to evaluating on a genuine ToolBench subset using the download pattern already established in our companion repository (`session-aware-toolbench-rerank`, `src/sessionrerank/data/download.py`, which pulls from the HuggingFace dataset `tuandunghcmut/toolbench-v1` via `snapshot_download`). We will run the same S1/S2/S3/S4 scenario structure (single-agent baseline, healthy mesh, 2/5-agent-failure, 20%-packet-loss) on a 200-query real-ToolBench sample instead of the synthetic fixture, using the same `MockLLM`-vs-real-backbone dual-track approach so a same-benchmark number exists for direct comparison against ToolLLaMA's published 66.7%. **Target artifacts:** `tables/table1_real_toolbench.csv`, `metrics/results_real_toolbench.json`. **Timeline:** 6 weeks (data download + fixture adaptation + full scenario re-run), not yet started.
2. Until that experiment lands, we will add an explicit construct-validity caveat wherever "ToolBench-syn" is mentioned in the paper (abstract, §IV-A) stating that it is a simplified proxy and that its absolute accuracy is not comparable to real-ToolBench pass rates.

---

### R2 Focus Area 2: Borda-count naming does not match the score-summing implementation; no free-text-to-rank conversion exists

**Reviewer concern:** "the code sums raw scores `w * float(s)`, never computes or uses `rank_a(r)` anywhere... nothing in the repository specifies how a real LLM's free-text completion would be parsed into either a numeric score or an ordinal rank."

**Status: Fixed (naming) + Fixed (true Borda variant added for comparison) + Planned (free-text parsing).**

1. **Naming corrected:** `src/agents.py::consensus_pick()`'s docstring and `README.md`'s "Core Equations" section have both been corrected to describe the function as a "weighted score-sum vote," not Borda count, matching what the code actually does.
2. **True rank-based Borda implemented for comparison:** we added `consensus_pick_borda()` to `src/agents.py`, which correctly implements \(\text{score}(r) = \sum_a w_a \cdot (|C| - \text{rank}_a(r))\). Run on the same 200-query synthetic fixture, it achieves **96.5% accuracy**, versus the score-sum version's 97.5% — both are far above the 44.0% single-agent baseline, confirming (as the reviewer's own Detailed Comment 2 anticipated) that the choice between these two aggregation rules is a second-order effect relative to the ensembling effect itself, at least under `MockLLM`'s scoring model.
3. **Free-text-to-rank conversion for real backbones remains unimplemented** and is the deeper gap the reviewer correctly identifies. We commit to a concrete design: each real-backbone agent will be prompted to emit a structured JSON ranking of the candidate tools (constrained decoding via the backbone's existing chat template) rather than free prose, which both `consensus_pick()` and `consensus_pick_borda()` can then consume directly without a separate parsing step. **Target artifact:** an updated `notebooks/build_notebook.py::HFBackbone.score_tool()` method. **Timeline:** bundled with the real-model ablation (5 weeks), not yet started.

---

### R2 Focus Area 3: Table 2 constitutes a category error against the reviewer's own knowledge of AutoGen/MetaGPT/CAMEL/LangGraph published results

**Status:** See Examiner-1 and R1-W3 responses above — fixed via `tables/table2_qualitative.md`. We note the CMU reviewer's independent domain knowledge (AutoGen's figures coming from math/coding multi-agent-debate settings, not tool selection; MetaGPT's 85.9% being HumanEval pass@1) corroborates, from a different angle, exactly the same conclusion the distributed-systems reviewer reached from a pure data-provenance angle. This convergence across two independent reviewers with different expertise increases our confidence that the fix (qualitative table, no shared numeric axis) is the correct one rather than an over-cautious response to a single reviewer's idiosyncratic concern.

---

### R2 Focus Area 4: Reproducibility — no frozen environment, no real committed backbone results

**Reviewer concern:** "no committed revision hash, quantization config verification, temperature/sampling parameters, or prompt templates are pinned or reported for that backbone... no evidence in the repository... indicates the notebook was ever executed to produce the reported numbers."

**Status: Fixed (dependency pinning) + Fixed (explicit disclosure) + Planned (real-model run).**

1. **`requirements.txt` added** (see R1-W4 above), pinning all real-backbone dependencies.
2. **README now discloses explicitly, in the Results section's "Important caveat" block**, that all currently committed numbers derive from `MockLLM`, that `metrics/results.json`'s `git_commit` field is `"n/a"`, and that no artifact in the repository shows the Kaggle notebook was ever executed — rather than allowing the three named backbones in the "HuggingFace Models Used in Notebook" table to imply that the committed results came from them.
3. **Planned:** the real-model ablation and real-ToolBench evaluation above (R1-W1/R2 Focus Area 1) will, when complete, record model revision hashes (`transformers` model card commit SHA), quantization config (4-bit, as already specified in `notebooks/build_notebook.py`'s `HFBackbone`), and sampling hyperparameters (temperature, top-p, max_new_tokens) for all three backbones, committed alongside the results artifact. **Timeline:** 5–6 weeks, bundled with the experiments above.

---

### R2 Focus Area 5: Scalability claims are untested beyond N=5

**Reviewer concern:** "Every one of the five scenarios uses exactly 5 agents... any statement in the paper implying the architecture 'scales' should be removed or explicitly qualified as untested."

**Authors' response:** Accepted. This is currently unaddressed in the repository and we do not have a partial fix to report yet.

1. **Planned experiment:** repeat the S1–S4 scenario structure at N ∈ {5, 10, 20, 40} agents, with the competence pool proportionally resampled and a proportional (~40%) agent-kill fraction applied at each N for the fault-tolerance condition, reporting accuracy, msgs/query, and latency p50/p95 at each N, and fitting the empirical message-cost curve against \(O(Nk\log N)\) (bundled with the R1-C4 gossip-fanout fitting commitment above). **Target artifact:** `metrics/results_scalability_sweep.json`, `tables/table_scalability.csv`. **Timeline:** 4 weeks, not yet started.
2. Until this experiment lands, we will add an explicit statement to `paper/mncd_paper.tex` §VI (Limitations) that all reported message-cost and fault-tolerance figures are measured only at N=5 and that scaling behavior beyond N=5 is untested, removing any language that could be read as an implicit scaling claim from the abstract's Cost Analysis discussion.

---

## Mandatory Fixes (per examiner instructions) — Consolidated Status

### Fix 1: Rewrite Table 2 as qualitative, or run a real same-benchmark baseline

**Status: Partially fixed, partially planned.** Qualitative rewrite (`tables/table2_qualitative.md`) is committed now. The real-baseline path (AutoGen GroupChat re-run on MNCD's own benchmark, `tables/table2_same_benchmark.csv`) is planned, 3-week timeline, not yet started.

### Fix 2: Add explicit "Baseline Specification" subsection

**Status: Fixed** in `README.md` (Results section caveat); LaTeX paper §IV subsection pending next revision pass (bundled with other §IV edits below).

### Fix 3: Same-model-mesh ablation

**Status: Fixed at the system layer** — `src/ablation_homogeneous.py` added, executed, and committed to `metrics/ablation_homogeneous.json`; result: homogeneous mesh 97.5% vs. heterogeneous mesh 97.5% (statistically indistinguishable), confirming the ensembling-not-heterogeneity finding. **Real-model version planned**, 5-week timeline, not yet started.

### Fix 4: Narrow novelty claim

**Status: Fixed** in `README.md`'s "Novel Contribution" section. LaTeX abstract wording update pending next revision pass.

### Fix 5: Related-work paragraph on coordination mechanisms (not just benchmark scores)

**Status: Planned.** `paper/mncd_paper.tex` §II (Related Work) currently describes AutoGen/MetaGPT/CAMEL/LangGraph's coordination mechanisms already (GroupChat manager, SOP assembly line, inception-prompted role pair, directed graph) but does not yet explicitly contrast each mechanism's consensus/aggregation approach against MNCD's weighted score-sum (or rank-Borda) vote. We commit to adding 1–2 sentences per framework on this specific axis in the next LaTeX revision pass. **Timeline:** 2 weeks (text-only change, no new experiments required), not yet started.

---

## Summary Table

| Issue | Status | Evidence / ETA |
|---|---|---|
| Table 2 mixes unrelated benchmarks (Examiner-1, R1-W3, R2-FA3) | **Fixed** (qualitative table) + **Planned** (real baseline) | `tables/table2_qualitative.md` (done); `tables/table2_same_benchmark.csv` via AutoGen GroupChat re-run, 3 weeks |
| S1 baseline tool access unspecified (Examiner-2) | **Fixed** (clarified: access is symmetric) | `README.md` Results caveat; LaTeX §IV subsection, next pass |
| Model heterogeneity confound (Examiner-3, R1-W1/W3, R2-FA5 overlap) | **Fixed** (system-layer ablation run) + **Planned** (real-model ablation) | `metrics/ablation_homogeneous.json` (homogeneous 97.5% ≈ heterogeneous 97.5%); real-LLM version 5 weeks |
| Distress channel never fires (R1-W2) | **Fixed** (disclosed + root-caused) + **Planned** (redesign + stress test) | `README.md` correction block; `metrics/results_distress_stress_test.json`, 4 weeks |
| No `requirements.txt` (R1-W4) | **Fixed** | `requirements.txt` added, root of repo |
| README R=5 escalation claim has no code (R1-C4) | **Fixed** (claim removed) | `README.md` Distress Trigger section |
| Gossip fanout claim asserted, not fitted (R1-C4) | **Planned** | Bundled with scalability sweep, 4 weeks |
| Karnataka scenario framed as live when synthetic (R1-C6) | **Fixed** | `README.md` Data Sources section; LaTeX §IV-A next pass |
| Novelty claim too broad (R1-W5) | **Fixed** | `README.md` Novel Contribution section; LaTeX abstract next pass |
| Borda-count naming mismatch; no free-text-to-rank path (R2-FA2) | **Fixed** (naming + true-Borda variant) + **Planned** (free-text parsing) | `src/agents.py::consensus_pick_borda()` (96.5% vs. 97.5%); `HFBackbone.score_tool()`, bundled with real-model ablation, 5 weeks |
| "ToolBench-syn" not a faithful proxy for real ToolBench (R2-FA1) | **Planned** | `metrics/results_real_toolbench.json`, 6 weeks |
| Reproducibility: no pinned env, no real-backbone artifact (R2-FA4) | **Fixed** (env pinning + disclosure) + **Planned** (real run) | `requirements.txt`; real-model results bundled above, 5–6 weeks |
| Scalability untested beyond N=5 (R2-FA5) | **Planned** | `metrics/results_scalability_sweep.json`, 4 weeks |
| Repository structure listing mismatched actual files | **Fixed** | `README.md` Repository Structure section corrected |
| MNCD name inconsistency (Diffusion vs. Distribution) | **Fixed** (disclosed as interchangeable) | `README.md` opening paragraph |

We are grateful to both reviewers for engagement rigorous enough to independently re-execute our own code rather than take the committed metrics at face value — this is precisely the level of scrutiny that surfaced the distress-channel and ensembling findings we consider the most important corrections in this response. We believe the fixes already committed, combined with the planned experiments and their concrete artifact paths and timelines above, chart a credible path to a defensible revision.
