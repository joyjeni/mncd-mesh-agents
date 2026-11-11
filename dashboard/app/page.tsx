import { C, Card } from '../components/ui';
import { loadAppWorld, AwHeadline, AwSetup, AwTable, AwCharts, AwO4, AwSecurity, AwEvidence } from '../components/appworld';
import { loadResults, EarlierHeadline, Architecture, Walkthrough, EarlierTable, EarlierCharts } from '../components/earlier';

const NAV = [
  ['#appworld', 'AppWorld'],
  ['#aw-results', 'Results'],
  ['#o4', 'O4 certified execution'],
  ['#security', 'Security controls'],
  ['#evidence', 'Evidence'],
  ['#earlier', 'Earlier experiments'],
  ['#artefacts', 'Artefacts'],
];

export default function Home() {
  const aw = loadAppWorld();
  const data = loadResults();

  return (
    <main style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>
      <header style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 12, letterSpacing: 1.2, textTransform: 'uppercase', color: C.muted, fontWeight: 600 }}>
          ACRS · Objective O4 · Byzantine-tolerant coordination for certified execution
        </div>
        <h1 style={{ fontSize: 32, fontWeight: 700, margin: '8px 0 0', color: C.ink, lineHeight: 1.2 }}>
          MNCD: from a peer-to-peer agent mesh to certified execution on AppWorld
        </h1>
        <p style={{ color: C.muted, marginTop: 10, fontSize: 15.5, lineHeight: 1.6, maxWidth: 820 }}>
          MNCD began as a decentralised mesh in which peer agents gossip context and vote on the right tool. In ACRS
          it is objective O4: before an agent changes anything, several candidate programs are run from a saved
          state, and only an outcome that a quorum agrees on is executed. Jenisha T · Ph.D. research, Ramaiah
          University of Applied Sciences · updated {aw.updated}.
        </p>
        <nav style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14 }}>
          {NAV.map(([href, label]) => (
            <a key={href} href={href} style={{ fontSize: 13, color: C.accentDark, textDecoration: 'none', border: `1px solid ${C.line}`, background: '#fff', borderRadius: 999, padding: '5px 12px' }}>{label}</a>
          ))}
        </nav>
      </header>

      <Card id="appworld" title="Latest: ACRS on AppWorld (development split, first full run)"
            intro="All four objectives and the policy check run in one agent loop with open-weight models on free GPUs, scored by AppWorld's own unit tests. Each configuration switches one part off, so every difference is attributable to that part.">
        <AwHeadline aw={aw} />
        <div style={{ height: 20 }} />
        <AwSetup aw={aw} focus="O4" />
      </Card>

      <Card id="aw-results" title="Outcome and cost of every configuration" intro="57 development tasks, one seed. The full-ACRS row is shaded.">
        <AwTable aw={aw} />
        <div style={{ height: 20 }} />
        <AwCharts aw={aw} />
      </Card>

      <Card id="o4" title="O4: certified execution inside ACRS">
        <AwO4 aw={aw} />
      </Card>

      <Card id="security" title="Security controls: policy as code"
            intro="What the agent may do is decided by explicit rules checked before anything runs, not by the model's judgement. These are the rules in the released harness.">
        <AwSecurity aw={aw} />
      </Card>

      <Card id="evidence" title="Paired tests and what the run supports" intro="Reported as they came out, including the results that are not significant.">
        <AwEvidence aw={aw} />
      </Card>

      <section id="earlier" style={{ margin: '40px 0 24px', padding: '20px 24px', borderRadius: 12, background: '#eef2f7', border: `1px solid ${C.line}` }}>
        <div style={{ fontSize: 12, letterSpacing: 1.2, textTransform: 'uppercase', color: C.muted, fontWeight: 600 }}>Earlier experiments · June 2026</div>
        <h2 style={{ fontSize: 24, margin: '6px 0 8px', color: C.ink }}>The decentralised mesh with simulated agents</h2>
        <p style={{ margin: 0, color: C.text, fontSize: 14.5, lineHeight: 1.6 }}>
          Before AppWorld, MNCD was tested with five simulated agents on 200 ToolBench-style queries and 15 Karnataka
          APMC mandi-price queries. The agents have a fixed competence parameter, so these accuracies measure the
          aggregation protocol under that model, not language-model quality. In the thesis numbering this work is
          objective O4 (it was called Objective 3 in the original notebooks). Generated {data.generated_at}.
        </p>
      </section>

      <Card title="Headline metrics (simulated agents)">
        <EarlierHeadline data={data} />
      </Card>

      <Card title="Architecture">
        <Architecture />
      </Card>

      <Card title="Algorithm walkthrough: query to consensus answer">
        <Walkthrough />
      </Card>

      <Card title="Main results: all scenarios">
        <EarlierTable data={data} />
      </Card>

      <Card title="Figures">
        <EarlierCharts data={data} />
      </Card>

      <Card title="Mathematical core">
        <p style={{ marginTop: 0 }}><b>Adaptive peer weight (EMA-smoothed):</b></p>
        <p style={{ background: C.panel, padding: 14, borderRadius: 8, border: `1px solid ${C.line}` }}>
          {`\\[ w_p^{(t+1)} = \\frac{(1-\\alpha)\\,s_p^{(t)} + \\alpha\\,\\mathbb{1}[\\text{success}]}{1 + \\ell_p^{(t)}/1000} \\]`}
        </p>
        <p><b>Gossip diffusion bound (Demers et al., 1987):</b> with fanout k ≥ 3, full
          dissemination across N nodes occurs in {` \\(O(\\log N)\\) `}rounds with high probability.</p>
        <p><b>Replication-resilient retrieval:</b> the probability that a critical key
          survives f independent node failures with replication factor R is</p>
        <p style={{ background: C.panel, padding: 14, borderRadius: 8, border: `1px solid ${C.line}` }}>
          {`\\[ P_{\\text{survive}}(R, f, N) \\;=\\; 1 - \\binom{N-R}{f} \\big/ \\binom{N}{f} \\]`}
        </p>
        <p><b>Consensus rule (weighted score-sum, as in <code>consensus_pick</code>; not Borda):</b></p>
        <p style={{ background: C.panel, padding: 14, borderRadius: 8, border: `1px solid ${C.line}` }}>
          {`\\[ \\hat{t} \\;=\\; \\arg\\max_{t \\in \\mathcal{T}} \\sum_{a \\in \\mathcal{A}} w_a \\cdot s_a(t \\mid q) \\]`}
        </p>
      </Card>

      <Card id="artefacts" title="Artefacts">
        <ul style={{ lineHeight: 1.8, marginTop: 0 }}>
          <li><a href="/data/appworld_dev.json">appworld_dev.json</a>: AppWorld aggregates behind every number in the first half of this page (no task text or API output)</li>
          <li><a href="https://github.com/joyjeni/acrs-appworld/tree/o4-provenance">joyjeni/acrs-appworld</a> (branch o4-provenance): the ACRS agent, the policy file and the Kaggle notebook</li>
          <li><a href="/data/results.json">results.json</a>: earlier mesh metrics (per scenario and per query)</li>
          <li><a href="/tables/table1_main_results.csv">table1_main_results.csv</a> / <a href="/tables/table1_main_results.md">.md</a></li>
          <li><a href="/tables/table2_sota_comparison.csv">table2_sota_comparison.csv</a> / <a href="/tables/table2_sota_comparison.md">.md</a></li>
          <li>Source: <a href="https://github.com/joyjeni/mncd-mesh-agents">github.com/joyjeni/mncd-mesh-agents</a> (src for the mesh, notebooks for the Kaggle notebook, paper for the manuscript)</li>
        </ul>
      </Card>

      <footer style={{ textAlign: 'center', color: C.faint, fontSize: 13, padding: '24px 0 8px' }}>
        MNCD · objective O4 of ACRS · earlier mesh v{data.version}
      </footer>
    </main>
  );
}
