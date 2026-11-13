import type { ReactNode } from 'react'
import type { SceneData } from '../api/session'
import { agentPanelState, evidenceChain } from '../planning/agentEvidence'
import { dataPillLabel, draftBannerText, headerStatus, latestEvaluation, layoutsFeasible, provenanceItems, provenanceStatus, scenarioSummary } from '../planning/shell'
import type { Workspace } from '../planning/useWorkspace'

/** Vision v2 application shell: navigation rail, context header and the Studio's floating panels. */

export type Screen = 'overview' | 'studio' | 'compare' | 'report'

const Icon = ({ children }: { children: ReactNode }) => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
)
const ICONS: Record<Screen, ReactNode> = {
  overview: <Icon><path d="M3 6.5 9 4l6 2.5L21 4v13.5L15 20l-6-2.5L3 20z" /><path d="M9 4v13.5M15 6.5V20" /></Icon>,
  studio: <Icon><path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" /></Icon>,
  compare: <Icon><rect x="3.5" y="4.5" width="7" height="15" rx="1.5" /><rect x="13.5" y="4.5" width="7" height="15" rx="1.5" /></Icon>,
  report: <Icon><path d="M7 3.5h7l4 4V20a.5.5 0 0 1-.5.5h-10A.5.5 0 0 1 7 20z" /><path d="M14 3.5V8h4M10 12h5M10 15.5h5" /></Icon>,
}

/** Rail labels follow the design; each accessible name keeps the screen's full title. */
export const SCREENS: readonly { id: Screen; label: string; title: string }[] = [
  { id: 'overview', label: 'Explore', title: 'Sheffield sites' },
  { id: 'studio', label: 'Studio', title: 'Planning studio' },
  { id: 'compare', label: 'Compare', title: 'Compare' },
  { id: 'report', label: 'Review', title: 'Review pack' },
]

export function NavigationRail({ screen, onSelect, connected }: { screen: Screen; onSelect: (s: Screen) => void; connected: boolean }) {
  return (
    <aside className="rail no-print">
      <div className="rail-logo" aria-label="CANOPY Sheffield" role="img">
        <svg viewBox="0 0 26 26" width="26" height="26" aria-hidden="true"><g fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="13" cy="9" r="5" /><circle cx="8" cy="13" r="3.5" /><circle cx="18" cy="13" r="3.5" /><path d="M13 14v9" /></g></svg>
      </div>
      <nav aria-label="Main navigation">
        {SCREENS.map(item => (
          <button key={item.id} type="button" className={`rail-item${screen === item.id ? ' active' : ''}`} aria-current={screen === item.id ? 'page' : undefined}
            aria-label={item.label === item.title ? item.title : `${item.label}: ${item.title}`} onClick={() => onSelect(item.id)}>
            {ICONS[item.id]}<span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="rail-foot" title={connected ? 'Local workspace connected' : 'Local workspace offline'}><span className={`status-dot${connected ? '' : ' warning'}`} /></div>
    </aside>
  )
}

const short = (value: string, n = 8) => (value.length > n + 1 ? `${value.slice(0, n)}…` : value)

/** Context header: site / scenario / revision, one status pill, the data-kind pill and the backend state. */
export function ContextHeader({ ws, screenTitle }: { ws: Workspace; screenTitle: string }) {
  const connected = ws.connection.status === 'connected'
  const evaluation = latestEvaluation(ws.runs, ws.currentRunIds.evaluation)
  const status = headerStatus({
    connected,
    revision: ws.scenario?.revision ?? null,
    draftDirty: ws.draftDirty,
    activeJob: ws.activeJob,
    jobStatusLost: ws.jobStatusLost,
    evaluationCurrentness: evaluation?.result ? ws.currentness(evaluation.result) : null,
  })
  const pill = dataPillLabel(connected, ws.site?.site_kind ?? null)
  return (
    <header className="topbar context-bar no-print">
      <span className="wordmark">CANOPY</span>
      <span className="bar-divider" aria-hidden="true" />
      <nav className="crumbs" aria-label="Context">
        <span>{ws.site?.name ?? screenTitle}</span>
        {ws.scenario && <><i aria-hidden="true">/</i><span className="mono" title={ws.scenario.scenario_id}>{short(ws.scenario.scenario_id)}</span><i aria-hidden="true">/</i><strong>Rev {ws.scenario.revision}{ws.draftDirty ? ' + draft' : ''}</strong></>}
      </nav>
      <span className={`status-pill sp-${status.tone}`} data-testid="header-status"><i aria-hidden="true" />{status.label}</span>
      <span className={`status-pill ${pill.synthetic ? 'sp-synthetic' : 'sp-muted'}`}><i aria-hidden="true" />{pill.label}</span>
      <span className="topbar-status" data-testid="backend-status"><span className={`status-dot${connected ? '' : ' warning'}`} /> {connected ? 'Local backend connected' : ws.connection.status === 'connecting' ? 'Connecting…' : 'Backend not connected'}</span>
    </header>
  )
}

/** The accepted scenario in one line, with the editor toggle (B07 / C01). */
export function ScenarioStrip({ ws, editorOpen, onToggle }: { ws: Workspace; editorOpen: boolean; onToggle: () => void }) {
  if (!ws.scenario) return null
  const s = scenarioSummary(ws.scenario)
  return (
    <section className="scenario-strip glass-dark" aria-label={`Accepted scenario revision ${ws.scenario.revision}`}>
      <span className="kicker">SCENARIO</span>
      <span>Budget <b className="mono">{s.budget}</b> <em>{s.basis}</em></span>
      <span className="strip-objective" title={s.objective}>Objective <b>{s.objective}</b></span>
      <span>Max trees <b className="mono">{s.maxTrees}</b></span>
      <span>Exclusions <b className="mono">{s.exclusions}</b></span>
      <button type="button" className="strip-button" aria-expanded={editorOpen} aria-controls="scenario-editor" onClick={onToggle}>
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /></svg>
        {editorOpen ? 'Close editor' : 'Edit scenario'}
      </button>
    </section>
  )
}

/** C02: the persistent signal that the visible result is not about the draft. */
export function DraftBanner({ ws, editorOpen, onReview }: { ws: Workspace; editorOpen: boolean; onReview: () => void }) {
  if (!ws.draftDirty || !ws.scenario) return null
  const shown = latestEvaluation(ws.runs, ws.currentRunIds.evaluation)?.result ?? null
  const text = draftBannerText(ws.scenario.revision, ws.draftChanges, shown ? shown.scenario_revision : null)
  return (
    <div className="draft-banner" role="status" data-testid="draft-banner">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M12 4 2.5 20h19z" /><path d="M12 10v4.5M12 17.2v.3" /></svg>
      <p><strong>{text.title}</strong> {text.detail}{ws.positionDirty && <> <span data-testid="ghost-note">The faded tree in the view marks the last evaluated position.</span></>}</p>
      {/* With the editor open, its own "Discard draft" is the one discard control (one button, one name). */}
      {!editorOpen && (
        <div className="banner-actions">
          <button type="button" className="banner-button" onClick={onReview}>Review draft</button>
          <button type="button" className="banner-button" onClick={ws.revertDraft}>Discard draft</button>
        </div>
      )}
    </div>
  )
}

/** Map key: only the layers the scene actually draws. */
export function MapKey({ scene, dirty, locationCount, optionCount, candidateMode }: { scene: SceneData | null; dirty: boolean; locationCount: number; optionCount: number; candidateMode: boolean }) {
  return (
    <section className="map-key glass-light" aria-labelledby="map-key-title">
      <div className="card-head"><h2 id="map-key-title" className="kicker">MAP KEY</h2>{candidateMode && <span className="mono caption" title="Distinct catalogue locations; one location can carry several profile entries">{locationCount} positions</span>}</div>
      <ul className="key-grid">
        <li><i className="legend-dot proposed" />Proposed tree</li>
        {dirty && <li><i className="legend-dot ghost" />Last evaluated position</li>}
        {scene?.kind === 'reference' && <><li><i className="legend-dot target" />Target receiver (represented area)</li><li><i className="legend-line sun" />Declared sun direction (input)</li></>}
        {scene?.kind === 'physical' && <><li><i className="legend-dot target" />Receiver samples ({scene.scene.samples.length})</li><li><i className="legend-line region" />Planting region</li></>}
        {candidateMode && <li><i className="legend-dot candidate" />Catalogue position</li>}
        {optionCount > 0 && <li><i className="legend-dot option" />Search option placements</li>}
      </ul>
      <p className="caption">{candidateMode ? 'Drag the tree to snap between catalogue positions' : 'Drag the tree to move it'} · drag elsewhere to orbit · scroll to zoom</p>
    </section>
  )
}

/** Planning agent (#74): a truthful unavailable state until the agent-run API (#73) exists. */
export function AgentPanel({ ws }: { ws: Workspace }) {
  const health = ws.connection.status === 'connected' ? ws.connection.health : null
  const state = agentPanelState(health)
  return (
    <section className="agent-bar glass-light" aria-labelledby="agent-title" data-testid="agent-panel">
      <div className="agent-head">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z" /></svg>
        <h2 id="agent-title">Planning agent</h2>
        <span className="status-pill sp-muted"><i aria-hidden="true" />NOT CONNECTED</span>
      </div>
      <p className="caption">{state.reason}</p>
      <p className="caption mono" data-testid="backend-operations">Backend operations: {health ? (health.available_operations.join(', ') || 'none') : 'unknown while offline'}</p>
      <form className="agent-form" onSubmit={e => e.preventDefault()}>
        <input aria-label="Question for the planning agent (unavailable)" placeholder="Available once the agent service is connected" disabled />
        <button type="submit" disabled aria-label="Send question (unavailable)">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
        </button>
      </form>
      <p className="caption">{!health ? 'Start the local backend to plan manually; the agent is not needed for that.' : state.manualEvaluateAvailable ? 'Manual planning works without it: use Evaluate planting.' : 'This backend offers no evaluate_layout operation.'}</p>
    </section>
  )
}

/** Provenance of the result the card shows (C04), from the stored Result only. */
export function ProvenanceStrip({ ws }: { ws: Workspace }) {
  const record = latestEvaluation(ws.runs, ws.currentRunIds.evaluation)
  const status = record?.result ? provenanceStatus(ws.currentness(record.result), record.result.scenario_revision) : null
  return (
    <footer className={`provenance-strip glass-dark mono${status && !status.current ? ' not-current' : ''}`} data-testid="provenance-strip">
      {record?.result && status
        ? <><b className={status.current ? 'prov-ok' : 'prov-warn'}>{status.label}</b>{provenanceItems(record.result, record.inputScenario, record.job.delivery).map(item => <span key={item}>{item}</span>)}</>
        : <span>No stored run yet: provenance appears with the first result</span>}
    </footer>
  )
}

/** Job → Result evidence for the shown evaluation, with #76's linkage checks. */
export function EvidenceChainDetails({ ws }: { ws: Workspace }) {
  const record = latestEvaluation(ws.runs, ws.currentRunIds.evaluation)
  if (!record?.result) return null
  const chain = evidenceChain(record.job, record.result, ws.currentness(record.result))
  // evaluate_layout reports "comparison_completed" (feasible: null), so its feasibility comes from its layouts.
  const infeasible = chain.ok && (chain.feasible === false || (chain.feasible === null && layoutsFeasible(record.result.layouts) === false))
  return (
    <details className="detail-section evidence-details" data-testid="evidence-chain">
      <summary>Evidence chain: job → result{infeasible ? ' · not feasible' : ''}</summary>
      {infeasible && <p className="error-box" data-testid="chain-infeasible">The backend computed this result, but it is not a feasible planting outcome. It is evidence, not a success.</p>}
      {chain.ok
        ? <dl className="chain">{chain.steps.map((s, i) => <div key={`${s.kind}-${i}`} className="chain-row"><dt>{s.label}</dt><dd className={s.kind === 'limitation' || s.kind === 'missing-metric' ? 'text-warning' : undefined}>{s.value}</dd></div>)}</dl>
        : <ul className="text-warning">{chain.problems.map(p => <li key={p}>{p}</li>)}</ul>}
    </details>
  )
}
