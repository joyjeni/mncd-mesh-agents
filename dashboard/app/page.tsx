import fs from 'fs';
import path from 'path';

type Scenario = {
  accuracy: number;
  latency_ms_p50: number;
  latency_ms_p95: number;
  uptime: number;
  msgs_per_query: number;
  replication_coverage: number;
  distress_rate: number;
  total_queries: number;
};

type Results = {
  version: string;
  generated_at: string;
  git_commit?: string;
  scenarios: Record<string, Scenario>;
};

function loadResults(): Results {
  const p = path.join(process.cwd(), 'public', 'data', 'results.json');
  const raw = fs.readFileSync(p, 'utf8');
  return JSON.parse(raw);
}

function Card({ children, title }: { children: React.ReactNode; title?: string }) {
  return (
    <section style={{
      background: '#fff', borderRadius: 12,
      padding: 24, marginBottom: 24,
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
    }}>
      {title && <h2 style={{ marginTop: 0, fontSize: 22, fontWeight: 600 }}>{title}</h2>}
      {children}
    </section>
  );
}

function KPI({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div style={{
      flex: 1, minWidth: 160, padding: 16,
      background: '#f8fafc', borderRadius: 10,
      border: '1px solid #e5e7eb',
    }}>
      <div style={{ fontSize: 12, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: '#111827', marginTop: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

const Th = ({ children }: { children: React.ReactNode }) => (
  <th style={{ textAlign: 'left', padding: '10px 12px', borderBottom: '2px solid #e5e7eb',
               fontSize: 13, color: '#374151', fontWeight: 600 }}>{children}</th>
);
const Td = ({ children, mono = false }: { children: React.ReactNode; mono?: boolean }) => (
  <td style={{ padding: '10px 12px', borderBottom: '1px solid #f1f5f9',
               fontSize: 14, fontFamily: mono ? 'ui-monospace, monospace' : 'inherit' }}>{children}</td>
);

export default function Home() {
  const data = loadResults();
  const s = data.scenarios;
  const base = s['S1_baseline_linear'];
  const mesh = s['S2_mesh_p2p'];
  const failed = s['S3_mesh_2_failed'];
  const loss = s['S4_mesh_20pct_loss'];
  const ka_mesh = s['S5_karnataka_apmc_mesh'];
  const ka_base = s['S6_karnataka_apmc_baseline'];

  return (
    <main style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 32, fontWeight: 700, margin: 0 }}>
          MNCD — Decentralized Context-Sharing Mesh
        </h1>
        <p style={{ color: '#6b7280', marginTop: 6 }}>
          Peer-to-peer multi-agent LLM coordination with gossip propagation, replicated context (R=3),
          and distress signaling. Generated {data.generated_at}{data.git_commit && ` · commit ${data.git_commit.slice(0,7)}`}.
        </p>
      </header>

      <Card title="Headline metrics (ToolBench-style, 5 agents)">
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <KPI label="Mesh accuracy" value={`${(mesh.accuracy * 100).toFixed(1)}%`} sub={`baseline ${(base.accuracy * 100).toFixed(1)}%`} />
          <KPI label="Uptime · 2/5 dead" value={`${(failed.uptime * 100).toFixed(0)}%`} sub={`accuracy ${(failed.accuracy * 100).toFixed(1)}%`} />
          <KPI label="Replication factor" value={mesh.replication_coverage.toFixed(2)} sub="target R = 3" />
          <KPI label="Latency p95 (mesh)" value={`${mesh.latency_ms_p95.toFixed(0)} ms`} sub={`p50 ${mesh.latency_ms_p50.toFixed(0)} ms`} />
          <KPI label="Karnataka APMC" value={`${(ka_mesh.accuracy * 100).toFixed(0)}%`} sub={`baseline ${(ka_base.accuracy * 100).toFixed(0)}%`} />
        </div>
      </Card>

      <Card title="Architecture">
        <p style={{ marginTop: 0 }}>
          Each agent is an equal peer with a pub/sub bus, gossip outbox, replicated K/V, and a failure
          detector. The mesh transports topic-tagged messages with TTL gossip propagation
          {' \\('}\\mathcal{`{O}`}(\\log N){' \\)'} rounds for full diffusion, per
          Demers et al. 1987).
        </p>
        <img src="/figures/architecture.png" alt="Architecture" style={{ width: '100%', borderRadius: 8 }} />
      </Card>

      <Card title="Algorithm walkthrough">
        <img src="/figures/algorithm_walkthrough.png" alt="Algorithm" style={{ width: '100%', borderRadius: 8 }} />
      </Card>

      <Card title="Main results — all scenarios">
        <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <Th>Scenario</Th>
              <Th>Accuracy</Th>
              <Th>Latency p50</Th>
              <Th>Latency p95</Th>
              <Th>Uptime</Th>
              <Th>Msgs/query</Th>
              <Th>Repl. factor</Th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(s).map(([name, m]) => (
              <tr key={name}>
                <Td mono>{name}</Td>
                <Td>{(m.accuracy * 100).toFixed(1)}%</Td>
                <Td>{m.latency_ms_p50.toFixed(1)} ms</Td>
                <Td>{m.latency_ms_p95.toFixed(1)} ms</Td>
                <Td>{(m.uptime * 100).toFixed(0)}%</Td>
                <Td>{m.msgs_per_query.toFixed(1)}</Td>
                <Td>{m.replication_coverage.toFixed(2)}</Td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </Card>

      <Card title="Figures (publication-ready)">
        <div style={{ display: 'grid', gap: 24, gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))' }}>
          {['fig1_accuracy', 'fig2_latency', 'fig3_uptime_replication',
            'fig4_message_cost', 'fig5_karnataka'].map(name => (
              <img key={name} src={`/figures/${name}.png`} alt={name}
                   style={{ width: '100%', borderRadius: 8, border: '1px solid #e5e7eb' }} />
          ))}
        </div>
      </Card>

      <Card title="Mathematical core">
        <p style={{ marginTop: 0 }}><b>Adaptive peer weight (EMA-smoothed):</b></p>
        <p style={{ background: '#f8fafc', padding: 14, borderRadius: 8, border: '1px solid #e5e7eb' }}>
          {`\\[ w_p^{(t+1)} = \\frac{(1-\\alpha)\\,s_p^{(t)} + \\alpha\\,\\mathbb{1}[\\text{success}]}{1 + \\ell_p^{(t)}/1000} \\]`}
        </p>
        <p><b>Gossip diffusion bound (Demers 1987):</b> with fanout k≥3, full
          dissemination across N nodes occurs in {' \\(O(\\log N)\\)'} rounds w.h.p.</p>
        <p><b>Replication-resilient retrieval:</b> probability that a critical key
          survives f independent node failures with replication factor R is
        </p>
        <p style={{ background: '#f8fafc', padding: 14, borderRadius: 8, border: '1px solid #e5e7eb' }}>
          {`\\[ P_{\\text{survive}}(R, f, N) \\;=\\; 1 - \\binom{N-R}{f} \\big/ \\binom{N}{f} \\]`}
        </p>
        <p><b>Consensus rule (weighted Borda):</b></p>
        <p style={{ background: '#f8fafc', padding: 14, borderRadius: 8, border: '1px solid #e5e7eb' }}>
          {`\\[ \\hat{t} \\;=\\; \\arg\\max_{t \\in \\mathcal{T}} \\sum_{a \\in \\mathcal{A}} w_a \\cdot s_a(t \\mid q) \\]`}
        </p>
      </Card>

      <Card title="Artefacts">
        <ul>
          <li><a href="/data/results.json">results.json</a> — full metrics dump (per-scenario + per-query)</li>
          <li><a href="/tables/table1_main_results.csv">table1_main_results.csv</a> / <a href="/tables/table1_main_results.md">.md</a></li>
          <li><a href="/tables/table2_sota_comparison.csv">table2_sota_comparison.csv</a> / <a href="/tables/table2_sota_comparison.md">.md</a></li>
          <li>Source: <a href="https://github.com/">GitHub repo</a> — see /src for the mesh, /notebooks for the Kaggle notebook, /paper for the LaTeX manuscript.</li>
        </ul>
      </Card>

      <footer style={{ textAlign: 'center', color: '#9ca3af', fontSize: 13, padding: '24px 0 8px' }}>
        MNCD v{data.version} · Decentralized Context-Sharing Mesh for Multi-Agent LLMs
      </footer>
    </main>
  );
}
