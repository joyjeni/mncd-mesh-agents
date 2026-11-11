// Shared building blocks for the MNCD dashboard (light theme, inline styles).
// Palette: one blue accent, a grey ramp, amber for reference lines. No red or green anywhere: on this
// site those would read as "faulty" and "correct".
import type { CSSProperties, ReactNode } from 'react';

export const C = {
  ink: '#111827',
  text: '#1f2937',
  muted: '#6b7280',
  faint: '#9ca3af',
  line: '#e5e7eb',
  panel: '#f8fafc',
  accent: '#2a78d6',
  accentDark: '#1c5cab',
  accentLight: '#86b6ef',
  accentTint: '#eaf2fc',
  grey1: '#b0afa7',
  grey2: '#8f8e88',
  grey3: '#6e6d68',
  grey4: '#4a4945',
  neutralFill: '#d6d5ce',
  reference: '#c98500',
};

export function Card({ children, title, id, intro }: { children: ReactNode; title?: string; id?: string; intro?: ReactNode }) {
  return (
    <section id={id} style={{
      background: '#fff', borderRadius: 12, padding: 24, marginBottom: 24,
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)', scrollMarginTop: 16,
    }}>
      {title && <h2 style={{ marginTop: 0, marginBottom: intro ? 6 : 16, fontSize: 22, fontWeight: 600, color: C.ink }}>{title}</h2>}
      {intro && <p style={{ marginTop: 0, marginBottom: 16, color: C.muted, fontSize: 14, lineHeight: 1.55 }}>{intro}</p>}
      {children}
    </section>
  );
}

export function KPI({ label, value, sub, accent = false }: { label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <div style={{
      flex: 1, minWidth: 180, padding: 16, background: accent ? C.accentTint : C.panel,
      borderRadius: 10, border: `1px solid ${accent ? '#cfe0f6' : C.line}`,
    }}>
      <div style={{ fontSize: 12, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: accent ? C.accentDark : C.ink, marginTop: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: C.muted, marginTop: 4, lineHeight: 1.45 }}>{sub}</div>}
    </div>
  );
}

export const Th = ({ children, right = false }: { children?: ReactNode; right?: boolean }) => (
  <th style={{ textAlign: right ? 'right' : 'left', padding: '10px 12px', borderBottom: `2px solid ${C.line}`,
               fontSize: 13, color: '#374151', fontWeight: 600, verticalAlign: 'bottom' }}>{children}</th>
);

export const Td = ({ children, mono = false, right = false, style }: { children?: ReactNode; mono?: boolean; right?: boolean; style?: CSSProperties }) => (
  <td style={{ padding: '10px 12px', borderBottom: '1px solid #f1f5f9', fontSize: 14, textAlign: right ? 'right' : 'left',
               fontFamily: mono ? 'ui-monospace, SFMono-Regular, Menlo, monospace' : 'inherit',
               fontVariantNumeric: mono ? 'tabular-nums' : undefined, whiteSpace: mono ? 'nowrap' : undefined,
               verticalAlign: 'top', ...style }}>{children}</td>
);

export function Legend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 16px', fontSize: 12, color: C.muted, marginBottom: 12 }}>
      {items.map((i) => (
        <span key={i.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: 2, background: i.color, display: 'inline-block' }} />
          {i.label}
        </span>
      ))}
    </div>
  );
}

export function ChartBox({ title, sub, children }: { title: string; sub?: ReactNode; children: ReactNode }) {
  return (
    <div style={{ border: `1px solid ${C.line}`, borderRadius: 10, padding: 16, background: '#fff' }}>
      <div style={{ fontSize: 15, fontWeight: 600, color: C.ink }}>{title}</div>
      {sub && <div style={{ fontSize: 12.5, color: C.muted, marginTop: 4, marginBottom: 12, lineHeight: 1.5 }}>{sub}</div>}
      {children}
    </div>
  );
}

/** One horizontal bar per row: label | bar | value. Bars may be stacked segments. */
export function HBars({ rows, max, labelWidth = 150, valueWidth = 90 }: {
  rows: { label: string; strong?: boolean; segments: { value: number; color: string; title: string }[]; text: string }[];
  max: number; labelWidth?: number; valueWidth?: number;
}) {
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      {rows.map((r) => (
        <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: labelWidth, flexShrink: 0, fontSize: 12.5, color: r.strong ? C.accentDark : C.text,
                        fontWeight: r.strong ? 600 : 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {r.label}
          </div>
          <div style={{ flex: 1, display: 'flex', gap: 2, height: 16 }}>
            {r.segments.filter((s) => s.value > 0).map((s, i, arr) => (
              <div key={i} title={s.title} style={{
                width: `${(100 * s.value) / max}%`, background: s.color, height: '100%',
                borderRadius: `${i === 0 ? 4 : 0}px ${i === arr.length - 1 ? 4 : 0}px ${i === arr.length - 1 ? 4 : 0}px ${i === 0 ? 4 : 0}px`,
              }} />
            ))}
          </div>
          <div style={{ width: valueWidth, flexShrink: 0, textAlign: 'right', fontSize: 12.5, color: C.text,
                        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontVariantNumeric: 'tabular-nums' }}>
            {r.text}
          </div>
        </div>
      ))}
    </div>
  );
}

export const grid2: CSSProperties = { display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 420px), 1fr))' };
