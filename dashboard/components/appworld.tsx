// ACRS on AppWorld (aggregates only: no task text or API output is published).
import fs from 'fs';
import path from 'path';
import { C, Card, KPI, Th, Td, Legend, ChartBox, HBars, grid2 } from './ui';

type Consensus = { voted_steps: number; certified: number; abstain_disagree: number; abstain_all_failed: number; candidate_executions: number; login_exempt: number };
type Config = {
  id: string; code: string; label: string; description: string; status: string;
  tgc_pct?: number; tgc_solved?: number; tgc_ci95?: number[]; sgc_pct?: number; sgc_solved?: number;
  steps_per_task?: number; tokens_m?: number; prompt_tokens_mean_per_task?: number; large_share_pct?: number;
  small_steps?: number; large_steps?: number; collateral_damage_tasks?: number; wall_min?: number;
  consensus?: Consensus; policy_denials?: number; provenance_denials?: number; recoverability?: number;
};
export type AppWorld = {
  title: string; updated: string; source: string; privacy: string;
  benchmark: { name: string; citation: string; apps: number; apis: number; split: string; tasks: number; scenarios: number; seeds: number; few_shot: number; grading: string };
  models: { large: string; small: string; serving: string };
  objectives: { id: string; name: string; short: string; repo?: string; appworld: string }[];
  configs: Config[];
  paired_mcnemar: { a: string; b: string; a_only: number; b_only: number; p: number }[];
  wilcoxon_prompt_tokens: { a: string; b: string; median_a: number; median_b: number; p: number }[];
  findings: { objective: string; rq: string; status: string; evidence: string; next: string }[];
  caveats: string[]; context: string; next_runs: string[];
  security_controls: { id: string; scope: string; rule: string }[];
};

export function loadAppWorld(): AppWorld {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'public', 'data', 'appworld_dev.json'), 'utf8'));
}

const get = (aw: AppWorld, id: string) => aw.configs.find((c) => c.id === id) as Config;
const mono = { fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' };

export function AwHeadline({ aw }: { aw: AppWorld }) {
  const full = get(aw, 'full');
  const noO4 = get(aw, 'no_o4');
  const cons = full.consensus as Consensus;
  const tokRatio = (full.tokens_m as number) / (noO4.tokens_m as number);
  const wallRatio = (full.wall_min as number) / (noO4.wall_min as number);
  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      <KPI accent label="Certified and committed" value={`${cons.certified} of ${cons.voted_steps}`}
           sub="state-changing steps put to a vote in full ACRS; the rest were withheld" />
      <KPI accent label="Collateral damage" value={`${full.collateral_damage_tasks} / ${aw.benchmark.tasks}`}
           sub={`tasks with O4, against ${noO4.collateral_damage_tasks} / ${aw.benchmark.tasks} without it (a single event)`} />
      <KPI label="Cost of certification" value={`${tokRatio.toFixed(1)}× tokens`}
           sub={`and ${wallRatio.toFixed(1)}× wall time of the same system without O4`} />
      <KPI label="Policy denials (G1)" value={`${full.policy_denials}`}
           sub="no task in this split triggered a rule, so G1 is not yet tested here" />
    </div>
  );
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: '7px 0', borderBottom: '1px solid #f1f5f9' }}>
      <span style={{ fontSize: 12.5, color: C.muted }}>{k}</span>
      <span style={{ fontSize: 13.5, color: C.text, textAlign: 'right' }}>{v}</span>
    </div>
  );
}

export function AwSetup({ aw, focus }: { aw: AppWorld; focus: string }) {
  const b = aw.benchmark;
  return (
    <>
      <div style={grid2}>
        <div>
          <Fact k="Benchmark" v={`${b.name} (${b.citation}): ${b.apps} apps, ${b.apis} APIs`} />
          <Fact k="Split" v={`${b.split}: ${b.tasks} tasks in ${b.scenarios} scenarios, ${b.seeds} seed`} />
          <Fact k="Graded by" v={b.grading} />
          <Fact k="Statistics" v="McNemar exact (success), Wilcoxon signed-rank (tokens), paired by task" />
        </div>
        <div>
          <Fact k="Large tier" v={aw.models.large} />
          <Fact k="Small tier" v={aw.models.small} />
          <Fact k="Serving" v={aw.models.serving} />
          <Fact k="Worked examples" v={`${b.few_shot} from the train split`} />
        </div>
      </div>
      <h3 style={{ fontSize: 16, margin: '22px 0 6px' }}>How each part acts on AppWorld</h3>
      <p style={{ marginTop: 0, color: C.muted, fontSize: 13.5, lineHeight: 1.55 }}>
        Within one step, O1 chooses the API documentation shown, O3 chooses the model, G1 checks the proposed code
        and O4 certifies any state change; O2 rewrites the history after the step. Each part has a switch; switched
        off, it becomes the usual analogue, so one agent gives the reference, the full system and every
        leave-one-out ablation.
      </p>
      <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))' }}>
        {aw.objectives.map((o) => {
          const f = o.id === focus || (focus === 'O4' && o.id === 'G1');
          return (
            <div key={o.id} style={{ border: `1px solid ${f ? '#cfe0f6' : C.line}`, background: f ? C.accentTint : C.panel, borderRadius: 10, padding: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: f ? C.accentDark : C.ink }}>
                {o.id} · {o.name}
                {o.id === focus && <span style={{ fontWeight: 400, fontSize: 11.5, color: C.accentDark }}> · this repository</span>}
              </div>
              <div style={{ fontSize: 12.5, color: C.muted, marginTop: 4, lineHeight: 1.5 }}>{o.appworld}</div>
            </div>
          );
        })}
      </div>
      <p style={{ fontSize: 12, color: C.faint, marginBottom: 0 }}>{aw.privacy} Source: {aw.source}.</p>
    </>
  );
}

export function AwTable({ aw }: { aw: AppWorld }) {
  const n = aw.benchmark.tasks;
  return (
    <>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 860 }}>
          <thead>
            <tr>
              <Th>Configuration</Th><Th right>Task success</Th><Th right>95% interval</Th><Th right>Scenarios</Th>
              <Th right>Steps / task</Th><Th right>Tokens (M)</Th><Th right>Steps on 8B</Th><Th right>Collateral damage</Th><Th right>Wall (min)</Th>
            </tr>
          </thead>
          <tbody>
            {aw.configs.map((c) => {
              const full = c.id === 'full';
              const bg = full ? { background: C.accentTint } : undefined;
              const label = (
                <Td style={bg}>
                  <div style={{ fontWeight: 600, color: full ? C.accentDark : C.ink }}>{c.label}</div>
                  <div style={{ fontSize: 11.5, color: C.faint }}>{c.description}</div>
                </Td>
              );
              if (c.status !== 'done') {
                return (
                  <tr key={c.id}>{label}<td colSpan={8} style={{ padding: '10px 12px', borderBottom: '1px solid #f1f5f9', color: C.muted, fontSize: 13, verticalAlign: 'top' }}>Scheduled on Kaggle; added here when the run finishes.</td></tr>
                );
              }
              return (
                <tr key={c.id}>
                  {label}
                  <Td mono right style={bg}>{c.tgc_pct?.toFixed(1)}% <span style={{ color: C.faint }}>({c.tgc_solved}/{n})</span></Td>
                  <Td mono right style={{ ...bg, color: C.muted }}>{c.tgc_ci95?.[0].toFixed(1)}–{c.tgc_ci95?.[1].toFixed(1)}</Td>
                  <Td mono right style={bg}>{c.sgc_solved}/{aw.benchmark.scenarios}</Td>
                  <Td mono right style={bg}>{c.steps_per_task?.toFixed(1)}</Td>
                  <Td mono right style={bg}>{c.tokens_m?.toFixed(2)}</Td>
                  <Td mono right style={bg}>{c.large_share_pct?.toFixed(1)}%</Td>
                  <Td mono right style={bg}>{c.collateral_damage_tasks}/{n}</Td>
                  <Td mono right style={{ ...bg, color: C.muted }}>{c.wall_min}</Td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p style={{ fontSize: 12.5, color: C.muted, lineHeight: 1.55, marginBottom: 0 }}>
        Task success (TGC): tasks whose unit tests all pass. Scenarios (SGC): groups of three related tasks fully
        solved. 95% interval: Wilson score interval. Collateral damage: tasks in which the agent changed state it
        was not asked to change. Wall time includes O4&apos;s candidate executions. The released harness uses the
        earlier objective numbering: <code>o4_only</code> is O2 only, <code>no_o4</code> is without O2,
        {' '}<code>no_o3</code> is without O4 and <code>no_o2</code> is without O3.
      </p>
    </>
  );
}

export function AwCharts({ aw }: { aw: AppWorld }) {
  const done = aw.configs.filter((c) => c.status === 'done');
  const ref = get(aw, 'reference');
  const max = 40;
  const x = (v: number) => `${(100 * v) / max}%`;
  const withO4 = done.filter((c) => c.consensus && c.consensus.voted_steps > 0);
  const maxVoted = Math.max(...withO4.map((c) => (c.consensus as Consensus).voted_steps));
  return (
    <div style={grid2}>
      <ChartBox title="Task success with 95% interval"
                sub="Every interval overlaps the reference agent (amber line): on 57 tasks no configuration is significantly better or worse.">
        <div style={{ display: 'grid', gap: 9 }}>
          {done.map((c) => {
            const full = c.id === 'full';
            const col = full ? C.accent : C.grey2;
            const [lo, hi] = c.tgc_ci95 as number[];
            return (
              <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 130, flexShrink: 0, fontSize: 12.5, color: full ? C.accentDark : C.text, fontWeight: full ? 600 : 400 }}>{c.label}</div>
                <div style={{ position: 'relative', flex: 1, height: 18 }} title={`${c.label}: ${c.tgc_pct}% (${c.tgc_solved}/57), 95% interval ${lo}–${hi}%`}>
                  <div style={{ position: 'absolute', top: 0, bottom: 0, left: x(ref.tgc_pct as number), borderLeft: `1.5px dashed ${C.reference}` }} />
                  <div style={{ position: 'absolute', top: 8, height: 2, left: x(lo), width: `calc(${x(hi)} - ${x(lo)})`, background: col, borderRadius: 1 }} />
                  <div style={{ position: 'absolute', top: 3, width: 12, height: 12, marginLeft: -6, left: x(c.tgc_pct as number), background: col, borderRadius: 6, boxShadow: '0 0 0 2px #fff' }} />
                </div>
                <div style={{ width: 48, textAlign: 'right', fontSize: 12.5, ...mono }}>{c.tgc_pct?.toFixed(1)}%</div>
              </div>
            );
          })}
          <div style={{ display: 'flex', gap: 10 }}>
            <div style={{ width: 130, flexShrink: 0 }} />
            <div style={{ position: 'relative', flex: 1, height: 14, fontSize: 10.5, color: C.faint }}>
              {[0, 10, 20, 30, 40].map((t) => (
                <span key={t} style={{ position: 'absolute', left: x(t), transform: 'translateX(-50%)' }}>{t}%</span>
              ))}
            </div>
            <div style={{ width: 48 }} />
          </div>
        </div>
      </ChartBox>

      <ChartBox title="What happened to the steps put to a vote"
                sub="O4 runs three candidate programs from a saved state. A step is executed only if at least two agree; most withheld steps were ones in which every candidate raised an error.">
        <Legend items={[
          { label: 'certified and committed', color: C.accentDark },
          { label: 'withheld: candidates disagreed', color: C.accentLight },
          { label: 'withheld: every candidate failed', color: C.neutralFill },
        ]} />
        <HBars max={maxVoted} labelWidth={130} valueWidth={110} rows={withO4.map((c) => {
          const k = c.consensus as Consensus;
          return {
            label: c.label, strong: c.id === 'full',
            segments: [
              { value: k.certified, color: C.accentDark, title: `${c.label}: ${k.certified} certified` },
              { value: k.abstain_disagree, color: C.accentLight, title: `${c.label}: ${k.abstain_disagree} disagreements` },
              { value: k.abstain_all_failed, color: C.neutralFill, title: `${c.label}: ${k.abstain_all_failed} with every candidate failing` },
            ],
            text: `${k.certified} / ${k.abstain_disagree} / ${k.abstain_all_failed}`,
          };
        })} />
      </ChartBox>
    </div>
  );
}

export function AwO4({ aw }: { aw: AppWorld }) {
  const full = get(aw, 'full');
  const noO4 = get(aw, 'no_o4');
  const k = full.consensus as Consensus;
  const finding = aw.findings.find((f) => f.rq === 'RQ4');
  return (
    <div style={grid2}>
      <div>
        <h3 style={{ fontSize: 16, marginTop: 0 }}>From a mesh vote to certified execution</h3>
        <p style={{ fontSize: 14, lineHeight: 1.6, color: C.text, marginTop: 0 }}>
          The earlier MNCD mesh let peers vote on the best tool. On AppWorld the vote moves to the <i>outcome</i>:
          when a proposed code block would change the world, ACRS samples further candidate programs, saves the
          world state, runs every candidate from that state, records the state-changing calls each one made and
          whether it raised an error, and restores the state and the agent&apos;s variables after each run.
        </p>
        <ol style={{ fontSize: 13.5, lineHeight: 1.6, color: C.text, paddingLeft: 20 }}>
          <li>A candidate&apos;s vote weight is 1 if it ran cleanly.</li>
          <li>With <i>n</i> = 3 candidates, the outcome signature with the largest weighted share is certified if
            the share reaches <i>θ</i> = 0.5 with at least two supporters.</li>
          <li>Only a certified outcome is executed for real. Otherwise ACRS abstains: nothing runs, the agent is told
            why, and the next step counts as risky, which biases O3 towards the large model.</li>
          <li>Login steps are exempt from the vote ({k.login_exempt} in full ACRS).</li>
        </ol>
      </div>
      <div>
        <h3 style={{ fontSize: 16, marginTop: 0 }}>Full ACRS on the 57 development tasks</h3>
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <tbody>
            <tr><Td>Steps put to a vote</Td><Td mono right>{k.voted_steps}</Td></tr>
            <tr><Td>Certified and committed</Td><Td mono right>{k.certified}</Td></tr>
            <tr><Td>Withheld: candidates disagreed</Td><Td mono right>{k.abstain_disagree}</Td></tr>
            <tr><Td>Withheld: every candidate raised an error</Td><Td mono right>{k.abstain_all_failed}</Td></tr>
            <tr><Td>Candidate executions</Td><Td mono right>{k.candidate_executions}</Td></tr>
            <tr><Td>Tokens / wall time</Td><Td mono right>{full.tokens_m} M / {full.wall_min} min</Td></tr>
            <tr><Td>Same system without O4</Td><Td mono right>{noO4.tokens_m} M / {noO4.wall_min} min</Td></tr>
            <tr><Td>Tasks with collateral damage</Td><Td mono right>{full.collateral_damage_tasks} with O4 · {noO4.collateral_damage_tasks} without</Td></tr>
          </tbody>
        </table>
        <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.55 }}>
          <b style={{ color: C.text }}>Status of RQ4: {finding?.status}.</b> {finding?.evidence} Next: {finding?.next}
        </p>
      </div>
    </div>
  );
}

export function AwSecurity({ aw }: { aw: AppWorld }) {
  return (
    <>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 640 }}>
          <thead><tr><Th>Rule</Th><Th>Layer</Th><Th>What it enforces</Th></tr></thead>
          <tbody>
            {aw.security_controls.map((r) => (
              <tr key={r.id}>
                <Td mono style={{ whiteSpace: 'nowrap' }}>{r.id}</Td>
                <Td style={{ whiteSpace: 'nowrap', color: C.muted }}>{r.scope}</Td>
                <Td>{r.rule}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p style={{ fontSize: 12.5, color: C.muted, lineHeight: 1.55, marginBottom: 0 }}>
        Rules deny by default, every condition must hold, and each rule is traced to a source and tested in both
        directions (allow and deny) in the offline test suite. The policy file is exportable to OPA Rego. In the
        development run no rule fired, so the AppWorld evidence for G1 is still to come; attack-success under
        injected instructions is part of the planned evaluation.
      </p>
    </>
  );
}

export function AwEvidence({ aw }: { aw: AppWorld }) {
  return (
    <>
      <div style={grid2}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ borderCollapse: 'collapse', width: '100%' }}>
            <thead><tr><Th>A vs B (McNemar exact)</Th><Th right>A only</Th><Th right>B only</Th><Th right>p</Th></tr></thead>
            <tbody>
              {aw.paired_mcnemar.map((p) => (
                <tr key={p.a + p.b}>
                  <Td>{p.a} <span style={{ color: C.faint }}>vs</span> {p.b}</Td>
                  <Td mono right>{p.a_only}</Td><Td mono right>{p.b_only}</Td><Td mono right style={{ color: C.muted }}>{p.p.toFixed(3)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ fontSize: 12.5, color: C.muted, lineHeight: 1.55 }}>
            Prompt tokens per task (median), Wilcoxon signed-rank:{' '}
            {aw.wilcoxon_prompt_tokens.map((w) => `${w.a} ${w.median_a.toLocaleString('en-GB')} vs ${w.b} ${w.median_b.toLocaleString('en-GB')}, p = ${w.p}`).join('; ')}.
          </p>
        </div>
        <div>
          <ul style={{ fontSize: 13.5, lineHeight: 1.6, color: C.text, paddingLeft: 18, marginTop: 0 }}>
            {aw.caveats.map((c) => <li key={c} style={{ marginBottom: 6 }}>{c}</li>)}
            <li>{aw.context}</li>
          </ul>
          <div style={{ fontSize: 12, fontWeight: 600, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.6 }}>Next runs</div>
          <ol style={{ fontSize: 13.5, lineHeight: 1.6, paddingLeft: 20, marginTop: 6 }}>
            {aw.next_runs.map((n) => <li key={n}>{n}</li>)}
          </ol>
        </div>
      </div>
      <div style={{ overflowX: 'auto', marginTop: 12 }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 760 }}>
          <thead><tr><Th>Question</Th><Th>Evidence from the development run</Th><Th>Status</Th><Th>Next</Th></tr></thead>
          <tbody>
            {aw.findings.map((f) => {
              const focus = f.objective.includes('O4');
              const bg = focus ? { background: C.accentTint } : undefined;
              return (
                <tr key={f.rq}>
                  <Td style={{ whiteSpace: 'nowrap', ...bg }}><b>{f.rq}</b> <span style={{ color: C.faint }}>· {f.objective}</span></Td>
                  <Td style={{ color: C.muted, ...bg }}>{f.evidence}</Td>
                  <Td style={bg}>{f.status}</Td>
                  <Td style={{ fontSize: 12.5, color: C.muted, ...bg }}>{f.next}</Td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

export { Card };
