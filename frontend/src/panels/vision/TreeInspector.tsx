import { useId } from 'react'
import type { Layout, Scenario, SiteBundle, TreeProfile } from '../../api/types'
import { MARGINAL_EXPLANATION, inspectTree, type DraftPlacement, type InspectorRow, type TreeEvidence } from '../../planning/treeInspector'
import './TreeInspector.css'

/**
 * B08 selected-tree inspector (display only; TreeEditor keeps the editing controls).
 * Shows what the contracts carry for one placement and says plainly what is not computed.
 */
export interface TreeInspectorProps {
  readonly placementId: string | null
  /** Layout holding the placement: ws.layout today, a search layout later. */
  readonly layout: Layout | null
  readonly site: SiteBundle | null
  readonly profiles: readonly TreeProfile[]
  readonly scenario: Scenario | null
  /** From layoutEvidence(ws.runs, layout, ws.scenario, ws.currentness, ws.currentRunIds.evaluation). */
  readonly evidence: TreeEvidence | null
  /** Unaccepted position bound to its placement; it only shows on that placement. */
  readonly draft: DraftPlacement | null
  readonly onClose?: () => void
}

function Rows({ rows }: { rows: readonly InspectorRow[] }) {
  return (
    <dl className="ti-rows">
      {rows.map(r => (
        <div key={r.label} className="ti-row">
          <dt>{r.label}</dt>
          <dd className={`ti-tone-${r.tone}${r.mono ? ' ti-mono' : ''}`}>
            {r.tag && <span className={`ti-tag ti-tag-${r.tone}`}>{r.tag}</span>}
            {r.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function TreeInspector({ placementId, layout, site, profiles, scenario, evidence, draft, onClose }: TreeInspectorProps) {
  const headingId = useId()
  const view = inspectTree({ placementId, layout, catalogue: site?.candidate_catalogue ?? [], profiles, scenario, evidence, draft })

  const kicker = (
    <div className="ti-kicker-row">
      <span className="ti-kicker">Selected tree</span>
      {onClose && (
        <button type="button" className="ti-close" onClick={onClose} aria-label="Close tree inspector">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      )}
    </div>
  )

  if (view.kind !== 'tree') {
    return (
      <section className="ti-root" aria-labelledby={headingId} data-testid="tree-inspector">
        {kicker}
        <h2 id={headingId} className="ti-title">{view.title}</h2>
        <p className={`ti-caption${view.kind === 'missing' ? ' ti-tone-warn' : ''}`} role={view.kind === 'missing' ? 'status' : undefined}>{view.detail}</p>
      </section>
    )
  }

  return (
    <section className="ti-root" aria-labelledby={headingId} data-testid="tree-inspector">
      {kicker}
      <div className="ti-title-row">
        <span className="ti-marker" aria-hidden="true" />
        <div className="ti-title-text">
          <h2 id={headingId} className="ti-title ti-mono-title">{view.title}</h2>
          <p className="ti-subtitle">{view.subtitle}</p>
        </div>
        <span className={`ti-pill ti-pill-${view.badge.tone}`}><i aria-hidden="true" />{view.badge.label}</span>
      </div>

      <div className="ti-tile" role="note" aria-label={`${view.marginal.label}: ${view.marginal.value}`} data-testid="tree-marginal">
        <div className="ti-tile-label">{view.marginal.label}{view.marginal.tag && <span className="ti-tag ti-tag-muted">{view.marginal.tag}</span>}</div>
        <div className="ti-tile-value">{view.marginal.value}</div>
        <p className="ti-caption">{MARGINAL_EXPLANATION}</p>
      </div>

      <Rows rows={view.position} />

      <details className="ti-section" open>
        <summary>Identity</summary>
        <Rows rows={view.identity} />
      </details>

      <details className="ti-section" open>
        <summary>Profile &amp; crown states</summary>
        <Rows rows={view.profile} />
        {view.states.length > 0 && (
          <ul className="ti-states">
            {view.states.map(s => (
              <li key={s.key} className={s.primary ? 'ti-state ti-state-primary' : 'ti-state'}>
                <div className="ti-state-head"><strong className="ti-mono">{s.heading}</strong>{s.primary && <span className="ti-tag ti-tag-ok">PRIMARY CASE</span>}</div>
                <span className="ti-mono">{s.crown}</span>
                <span className="ti-mono">{s.trunk}</span>
                <span>{s.light}</span>
                <span className="ti-caption">Used by: {s.usedBy}</span>
              </li>
            ))}
          </ul>
        )}
      </details>

      <details className="ti-section" open>
        <summary>Stored evaluation of this layout</summary>
        {view.evaluation.length > 0 && <Rows rows={view.evaluation} />}
        <p className="ti-caption">{view.evaluationNote}</p>
        {view.evaluation.length > 0 && (
          <>
            <h3 className="ti-subhead">Constraints</h3>
            <p className="ti-caption">{view.constraintNote}</p>
            {view.constraints.length > 0 && (
              <ul className="ti-constraints">
                {view.constraints.map((c, i) => (
                  <li key={`${c.rule}-${i}`} className="ti-constraint">
                    <span className="ti-constraint-rule">{c.rule}</span>
                    <span className={`ti-status ti-status-${c.status}`}>{c.statusLabel}</span>
                    {c.detail && <span className="ti-caption ti-mono">{c.detail}</span>}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </details>
    </section>
  )
}

export default TreeInspector
