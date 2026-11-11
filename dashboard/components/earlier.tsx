// Earlier MNCD experiments (June 2026): simulated agents on ToolBench-style and Karnataka APMC queries.
// Charts and diagrams are drawn from results.json so that the colours follow the site palette.
import fs from 'fs';
import path from 'path';
import { C, KPI, Th, Td, ChartBox, HBars, Legend, grid2 } from './ui';

type Scenario = {
  accuracy: number; latency_ms_p50: number; latency_ms_p95: number; uptime: number;
  msgs_per_query: number; replication_coverage: number; distress_rate: number; total_queries: number;
};
type Results = {
  version: string; generated_at: string; git_commit?: string;
  scenarios: Record<string, Scenario>;
  raw_per_query: Record<string, { qid: string; correct: boolean; latency_ms: number; confidence: number }[]>;
};

export function loadResults(): Results {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'public', 'data', 'results.json'), 'utf8'));
}

const LABEL: Record<string, string> = {
  S1_baseline_linear: 'Baseline (1 agent)',
  S2_mesh_p2p: 'Mesh (5 agents)',
  S3_mesh_2_failed: 'Mesh, 2/5 failed',
  S4_mesh_20pct_loss: 'Mesh, 20% loss',
  S5_karnataka_apmc_mesh: 'Karnataka APMC, mesh',
  S6_karnataka_apmc_baseline: 'Karnataka APMC, baseline',
};

function wilson(k: number, n: number): [number, number] {
  const z = 1.959964, p = k / n, d = 1 + (z * z) / n;
  const c = (p + (z * z) / (2 * n)) / d;
  const h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  return [100 * Math.max(0, c - h), 100 * Math.min(1, c + h)];
}

function quantile(sorted: number[], q: number) {
  const i = (sorted.length - 1) * q, lo = Math.floor(i), hi = Math.ceil(i);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (i - lo);
}

export function EarlierHeadline({ data }: { data: Results }) {
  const s = data.scenarios;
  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      <KPI label="Mesh accuracy" value={`${(s.S2_mesh_p2p.accuracy * 100).toFixed(1)}%`} sub={`single agent ${(s.S1_baseline_linear.accuracy * 100).toFixed(1)}%`} />
      <KPI label="With 2 of 5 agents down" value={`${(s.S3_mesh_2_failed.accuracy * 100).toFixed(1)}%`} sub={`uptime ${(s.S3_mesh_2_failed.uptime * 100).toFixed(0)}%`} />
      <KPI label="Replicas per key" value={s.S2_mesh_p2p.replication_coverage.toFixed(2)} sub="target R = 3" />
      <KPI label="Karnataka APMC (15 queries)" value={`${(s.S5_karnataka_apmc_mesh.accuracy * 100).toFixed(0)}%`} sub={`single agent ${(s.S6_karnataka_apmc_baseline.accuracy * 100).toFixed(0)}%`} />
    </div>
  );
}

/* Architecture: five equal peers, fully connected, with the components every node carries. */
export function Architecture() {
  const names = ['A0 Planner', 'A1 Retriever', 'A2 Executor', 'A3 Verifier', 'A4 Specialist'];
  const cx = 260, cy = 210, r = 150;
  const pts = names.map((_, i) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  });
  const edges: [number, number][] = [];
  for (let i = 0; i < 5; i++) for (let j = i + 1; j < 5; j++) edges.push([i, j]);
  return (
    <div style={grid2}>
      <svg viewBox="0 0 560 430" role="img" aria-label="Five equal peer agents, fully connected, receive a query and emit a consensus answer" style={{ width: '100%', height: 'auto' }}>
        <defs>
          <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={C.grey3} />
          </marker>
        </defs>
        {edges.map(([i, j]) => (
          <line key={`${i}-${j}`} x1={pts[i][0]} y1={pts[i][1]} x2={pts[j][0]} y2={pts[j][1]} stroke={C.grey1} strokeWidth="1.2" />
        ))}
        {pts.map(([x, y], i) => (
          <g key={names[i]}>
            <rect x={x - 62} y={y - 22} width="124" height="44" rx="8" fill={C.accentTint} stroke={C.accent} strokeWidth="1.4" />
            <text x={x} y={y - 3} textAnchor="middle" fontSize="13" fontWeight="600" fill={C.ink}>{names[i]}</text>
            <text x={x} y={y + 13} textAnchor="middle" fontSize="10.5" fill={C.muted}>LLM + MeshNode</text>
          </g>
        ))}
        <rect x="398" y="8" width="156" height="44" rx="8" fill={C.panel} stroke={C.grey3} />
        <text x="476" y="27" textAnchor="middle" fontSize="12.5" fontWeight="600" fill={C.ink}>Query in</text>
        <text x="476" y="42" textAnchor="middle" fontSize="10.5" fill={C.muted}>ToolBench / APMC schema</text>
        <line x1="398" y1="40" x2={pts[0][0] + 64} y2={pts[0][1] - 6} stroke={C.grey3} strokeWidth="1.4" markerEnd="url(#arr)" />
        <rect x="400" y="372" width="150" height="48" rx="8" fill={C.panel} stroke={C.grey3} />
        <text x="475" y="392" textAnchor="middle" fontSize="12.5" fontWeight="600" fill={C.ink}>Consensus answer</text>
        <text x="475" y="408" textAnchor="middle" fontSize="10.5" fill={C.muted}>weighted vote, rank.update</text>
        <line x1={pts[2][0] + 40} y1={pts[2][1] + 22} x2="398" y2="392" stroke={C.grey3} strokeWidth="1.4" markerEnd="url(#arr)" />
      </svg>
      <div style={{ fontSize: 13.5, lineHeight: 1.6 }}>
        <p style={{ marginTop: 0 }}>
          Every agent is an equal peer. Updates spread by push gossip (TTL 6) in O(log N) rounds, and critical
          context is replicated on three nodes, so the mesh keeps answering when nodes fail.
        </p>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>Each MeshNode carries</div>
        <ul style={{ marginTop: 0, paddingLeft: 18 }}>
          <li>a pub/sub bus and a gossip outbox</li>
          <li>a replicated key/value store (R = 3)</li>
          <li>a failure detector and a distress channel</li>
        </ul>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>Topics</div>
        <div style={{ fontFamily: 'ui-monospace, monospace', fontSize: 12.5, color: C.muted }}>
          plan.candidate · tool.evidence · rank.update · answer.partial · answer.final · __distress__
        </div>
      </div>
    </div>
  );
}

const STEPS: [string, string][] = [
  ['Query enters via any peer (A0)', 'Topic-tagged message msg = (qid, query, tools[])'],
  ["A0 publishes on 'plan.candidate'", 'Local subscribers fire; the outbox queues it for fanout = 3 peers'],
  ['Gossip round (push)', 'Each peer relays by weighted sampling: w_p = success_p / (1 + lat_p / 1 s)'],
  ['All live peers score the tools in parallel', 'score_tool(query, tools[]) gives a ranking and a confidence'],
  ["Each peer publishes 'rank.update'", "If confidence < τ = 0.55 it emits a '__distress__' broadcast"],
  ['Distress responders give a second opinion', 'Helpers add weight to under-represented votes'],
  ['Consensus pick', 'argmax over Σ_agents w_a · score_a(tool); replicated R = 3 to the K/V store'],
  ['Failure-detector tick (every round)', 'If last_seen(p) > 4 s, p is suspected and later fanout skips it'],
  ["Answer emitted on 'answer.final'", 'Stored under plan::qid on three replicas, so it survives two failures'],
];

export function Walkthrough() {
  return (
    <ol style={{ margin: 0, paddingLeft: 0, listStyle: 'none', display: 'grid', gap: 8 }}>
      {STEPS.map(([t, d], i) => (
        <li key={t} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', border: `1px solid ${C.line}`, borderRadius: 10, padding: '10px 12px', background: C.panel }}>
          <span style={{ flexShrink: 0, width: 26, height: 26, borderRadius: 13, background: C.accentTint, color: C.accentDark, fontWeight: 700, fontSize: 13, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>{i + 1}</span>
          <span>
            <span style={{ fontWeight: 600, fontSize: 14 }}>{t}</span>
            <span style={{ display: 'block', fontSize: 12.5, color: C.muted, fontFamily: 'ui-monospace, monospace', marginTop: 2 }}>{d}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}

export function EarlierTable({ data }: { data: Results }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 760 }}>
        <thead>
          <tr><Th>Scenario</Th><Th right>Accuracy</Th><Th right>Wilson 95% CI</Th><Th right>Latency p50</Th><Th right>Latency p95</Th><Th right>Uptime</Th><Th right>Msgs/query</Th><Th right>Replicas</Th></tr>
        </thead>
        <tbody>
          {Object.entries(data.scenarios).map(([name, m]) => {
            const k = Math.round(m.accuracy * m.total_queries);
            const [lo, hi] = wilson(k, m.total_queries);
            return (
              <tr key={name}>
                <Td>{LABEL[name] ?? name} <span style={{ color: C.faint, fontSize: 12 }}>· n = {m.total_queries}</span></Td>
                <Td mono right>{(m.accuracy * 100).toFixed(1)}%</Td>
                <Td mono right style={{ color: C.muted }}>{lo.toFixed(1)}–{hi.toFixed(1)}</Td>
                <Td mono right>{m.latency_ms_p50.toFixed(1)} ms</Td>
                <Td mono right>{m.latency_ms_p95.toFixed(1)} ms</Td>
                <Td mono right>{(m.uptime * 100).toFixed(0)}%</Td>
                <Td mono right>{m.msgs_per_query.toFixed(1)}</Td>
                <Td mono right>{m.replication_coverage.toFixed(2)}</Td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function EarlierCharts({ data }: { data: Results }) {
  const s = data.scenarios;
  const core = ['S1_baseline_linear', 'S2_mesh_p2p', 'S3_mesh_2_failed', 'S4_mesh_20pct_loss'];
  const faults = ['S2_mesh_p2p', 'S3_mesh_2_failed', 'S4_mesh_20pct_loss'];
  const box = core.map((k) => {
    const v = data.raw_per_query[k].map((q) => q.latency_ms).sort((a, b) => a - b);
    return { k, min: v[0], q1: quantile(v, 0.25), med: quantile(v, 0.5), q3: quantile(v, 0.75), max: v[v.length - 1] };
  });
  const lmax = 140;
  const lx = (v: number) => `${(100 * v) / lmax}%`;
  return (
    <div style={grid2}>
      <ChartBox title="Tool-selection accuracy (200 ToolBench-style queries)" sub="Simulated agents; blue = the mesh, grey = a single agent.">
        <HBars max={100} labelWidth={140} valueWidth={60} rows={core.map((k) => ({
          label: LABEL[k], strong: false,
          segments: [{ value: s[k].accuracy * 100, color: k === 'S1_baseline_linear' ? C.grey2 : C.accent, title: `${LABEL[k]}: ${(s[k].accuracy * 100).toFixed(1)}%` }],
          text: `${(s[k].accuracy * 100).toFixed(1)}%`,
        }))} />
      </ChartBox>

      <ChartBox title="End-to-end latency per query" sub="Box: middle half of the 200 queries; line: median; whiskers: minimum and maximum. The single agent answers in about 5 ms.">
        <div style={{ display: 'grid', gap: 10 }}>
          {box.map((b) => (
            <div key={b.k} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 140, flexShrink: 0, fontSize: 12.5 }}>{LABEL[b.k]}</div>
              <div style={{ position: 'relative', flex: 1, height: 18 }} title={`${LABEL[b.k]}: median ${b.med.toFixed(1)} ms, middle half ${b.q1.toFixed(1)}–${b.q3.toFixed(1)} ms, range ${b.min.toFixed(1)}–${b.max.toFixed(1)} ms`}>
                <div style={{ position: 'absolute', top: 8, height: 1.5, left: lx(b.min), width: `calc(${lx(b.max)} - ${lx(b.min)})`, background: C.grey2 }} />
                <div style={{ position: 'absolute', top: 2, height: 14, left: lx(b.q1), width: `max(3px, calc(${lx(b.q3)} - ${lx(b.q1)}))`, background: b.k === 'S1_baseline_linear' ? C.grey1 : C.accentLight, borderRadius: 3 }} />
                <div style={{ position: 'absolute', top: 0, height: 18, left: lx(b.med), width: 2, background: C.ink }} />
              </div>
              <div style={{ width: 60, textAlign: 'right', fontSize: 12.5, fontFamily: 'ui-monospace, monospace' }}>{b.med.toFixed(0)} ms</div>
            </div>
          ))}
          <div style={{ display: 'flex', gap: 10 }}>
            <div style={{ width: 140, flexShrink: 0 }} />
            <div style={{ position: 'relative', flex: 1, height: 14, fontSize: 10.5, color: C.faint }}>
              {[0, 35, 70, 105, 140].map((t) => <span key={t} style={{ position: 'absolute', left: lx(t), transform: 'translateX(-50%)' }}>{t}</span>)}
            </div>
            <div style={{ width: 60 }} />
          </div>
        </div>
      </ChartBox>

      <ChartBox title="Under faults: uptime and replication" sub="Two measures, two panels. Replication stays near the target of three copies per critical key until packet loss rises.">
        <div style={{ fontSize: 12, color: C.muted, marginBottom: 6 }}>Uptime</div>
        <HBars max={100} labelWidth={140} valueWidth={60} rows={faults.map((k) => ({
          label: LABEL[k], segments: [{ value: s[k].uptime * 100, color: C.accent, title: `${LABEL[k]}: ${(s[k].uptime * 100).toFixed(0)}%` }], text: `${(s[k].uptime * 100).toFixed(0)}%`,
        }))} />
        <div style={{ fontSize: 12, color: C.muted, margin: '14px 0 6px' }}>Replicas per critical key (target 3)</div>
        <HBars max={3} labelWidth={140} valueWidth={60} rows={faults.map((k) => ({
          label: LABEL[k], segments: [{ value: s[k].replication_coverage, color: C.grey3, title: `${LABEL[k]}: ${s[k].replication_coverage.toFixed(2)}` }], text: s[k].replication_coverage.toFixed(2),
        }))} />
      </ChartBox>

      <ChartBox title="Gossip cost per query" sub="Messages published and received per query. Fewer live peers send fewer messages; packet loss cuts deliveries.">
        <HBars max={Math.max(...faults.map((k) => s[k].msgs_per_query))} labelWidth={140} valueWidth={60} rows={faults.map((k) => ({
          label: LABEL[k], segments: [{ value: s[k].msgs_per_query, color: C.grey3, title: `${LABEL[k]}: ${s[k].msgs_per_query.toFixed(1)} messages` }], text: s[k].msgs_per_query.toFixed(1),
        }))} />
        <div style={{ height: 18 }} />
        <div style={{ fontSize: 15, fontWeight: 600, color: C.ink }}>Karnataka APMC mandi-price tool selection</div>
        <div style={{ fontSize: 12.5, color: C.muted, margin: '4px 0 10px' }}>15 queries on 15 endpoints: too few to separate methods closer than about 30 points.</div>
        <Legend items={[{ label: 'mesh (5 agents)', color: C.accent }, { label: 'single agent', color: C.grey2 }]} />
        <HBars max={100} labelWidth={180} valueWidth={60} rows={['S5_karnataka_apmc_mesh', 'S6_karnataka_apmc_baseline'].map((k) => ({
          label: LABEL[k], segments: [{ value: s[k].accuracy * 100, color: k.endsWith('mesh') ? C.accent : C.grey2, title: `${LABEL[k]}: ${(s[k].accuracy * 100).toFixed(1)}%` }], text: `${(s[k].accuracy * 100).toFixed(1)}%`,
        }))} />
      </ChartBox>
    </div>
  );
}
