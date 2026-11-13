import { useEffect, useState } from 'react'
import type { Result, TreeProfile, TreeState, Vec3 } from '../api/types'
import type { DeclarationCheck } from '../api/session'
import type { TransformCheck } from '../scene/transform'
import {
  CURRENTNESS_LABEL, EDIT_LIMIT_M, samePosition, EXECUTION_MODE_LABEL, clampPosition, describeJob, formatPence, formatValue,
  primaryMetric, unitLabel, type Currentness,
} from '../planning/evaluation'
import type { RunRecord, Workspace } from '../planning/useWorkspace'

function describeAttenuation(a: unknown): string {
  const v = a as { mode?: string; transmission?: number | null } | null
  if (!v?.mode) return 'not stated'
  return v.mode === 'opaque' ? 'opaque (assumed)' : v.mode === 'fixed_crossing' ? `fixed crossing, transmission ${v.transmission ?? '—'} (assumed)` : v.mode
}

const short = (value: string, n = 10) => (value.length > n + 1 ? `${value.slice(0, n)}…` : value)

export function SiteStatus({ ws, transform }: { ws: Workspace; transform: TransformCheck | null }) {
  const { connection, site, declaration, scenario } = ws
  return (
    <div className="detail-section">
      <span className="section-kicker">SITE &amp; BACKEND</span>
      <h2>{site ? site.name : 'No site loaded'}</h2>
      {connection.status === 'connected' ? (
        <>
          <Row label="Backend" value={`CANOPY ${connection.health.version} · worker ${connection.health.worker_mode}`} />
          <Row label="Operations" value={connection.health.available_operations.join(', ') || 'none'} warn={!connection.health.available_operations.includes('evaluate_layout')} />
          <Row label="Site kind" value={site?.site_kind === 'synthetic_test' ? 'Synthetic test (not Sheffield)' : site?.site_kind ?? '—'} warn={site?.site_kind === 'synthetic_test'} />
          <Row label="Scenario" value={scenario ? `${short(scenario.scenario_id, 8)} · rev ${scenario.revision}` : '—'} />
          <Row label="Geometry bytes" value={declarationLabel(declaration)} warn={declaration?.status !== 'verified'} />
          <Row label="Viewer frame" value={transform ? (transform.status === 'matches-provisional' ? 'Matches provisional' : transform.status === 'identity-unresolved' ? 'Identity in SiteBundle — provisional used' : 'Unsupported') : '—'} warn={transform?.status !== 'matches-provisional'} />
          {transform && transform.status !== 'matches-provisional' && <p className="fine-print">{transform.detail}</p>}
          {declaration && declaration.status !== 'verified' && <p className="fine-print text-warning">{declaration.reason}</p>}
        </>
      ) : (
        <p className="fine-print">{connection.status === 'connecting' ? 'Connecting to the local backend…' : connection.reason}</p>
      )}
      {connection.status !== 'connected' && connection.status !== 'connecting' && (
        <button type="button" className="secondary-action" onClick={ws.reload}>Retry connection</button>
      )}
    </div>
  )
}

function declarationLabel(check: DeclarationCheck | null) {
  if (!check) return 'Not supplied'
  // A byte-hash match of the geometry file, not a statement about the site itself.
  if (check.status === 'verified') return `Hash matches · sha256 ${short(check.sha256, 8)}`
  return check.status === 'mismatch' ? 'Hash mismatch — not drawn' : check.status === 'missing' ? 'Asset missing — not drawn' : 'Invalid — not drawn'
}

function Row({ label, value, warn = false }: { label: string; value: string; warn?: boolean }) {
  return <div className="readiness-row"><span>{label}</span><strong className={warn ? 'text-warning' : undefined}>{value}</strong></div>
}

function NumberField({ label, value, onCommit, disabled }: { label: string; value: number; onCommit: (v: number) => void; disabled: boolean }) {
  const [text, setText] = useState(String(value))
  useEffect(() => setText(String(value)), [value])
  const commit = () => {
    const parsed = Number(text)
    if (text.trim() === '' || !Number.isFinite(parsed)) setText(String(value))
    else onCommit(parsed)
  }
  return (
    <label className="number-field">
      <span>{label}</span>
      <input type="number" step="0.1" min={-EDIT_LIMIT_M} max={EDIT_LIMIT_M} inputMode="decimal" value={text} disabled={disabled}
        onChange={e => setText(e.target.value)} onBlur={commit} onKeyDown={e => { if (e.key === 'Enter') commit() }} />
      <em>m</em>
    </label>
  )
}

export function TreeEditor({ ws, profile, state, caseState }: { ws: Workspace; profile: TreeProfile | null; state: TreeState | null; caseState: string | null }) {
  const { draftPosition: draft, committedPosition: committed, positionDirty: draftDirty } = ws
  const editable = ws.connection.status === 'connected' && Boolean(draft)
  const catalogue = ws.site?.candidate_catalogue ?? []
  return (
    <div className="detail-section">
      <span className="section-kicker">PROPOSED TREE</span>
      <h3 className="section-title">{ws.placementId ?? 'No placement'} {draftDirty && <span className="tag tag-warning">UNSAVED MOVE</span>}</h3>
      {catalogue.length > 0 ? (
        <fieldset className="candidate-list" aria-label="Catalogue position for the proposed tree">
          {catalogue.map(c => {
            const checked = Boolean(draft && samePosition(c.position_enu_m as Vec3, draft))
            return (
              <label key={c.candidate_id} className={`case-option${checked ? ' active' : ''}`}>
                <input type="radio" name="candidate" value={c.candidate_id} checked={checked} disabled={!editable} onChange={() => ws.setDraftPosition(c.position_enu_m as Vec3)} />
                <span><strong>{c.candidate_id}</strong> · E {c.position_enu_m[0]}, N {c.position_enu_m[1]} · {c.plantability_status}</span>
              </label>
            )
          })}
          <p className="fine-print">This site has a candidate catalogue, so the backend evaluates catalogue positions only. Drag snaps to the nearest position; arrow keys step to the next one in that direction.</p>
        </fieldset>
      ) : (
        <>
          <div className="field-grid">
            <NumberField label="East" value={draft?.[0] ?? 0} disabled={!editable} onCommit={v => draft && ws.setDraftPosition(clampPosition([v, draft[1], draft[2]]))} />
            <NumberField label="North" value={draft?.[1] ?? 0} disabled={!editable} onCommit={v => draft && ws.setDraftPosition(clampPosition([draft[0], v, draft[2]]))} />
          </div>
          <p className="fine-print">Drag the tree in the view, or focus the view and use arrow keys (0.1 m; Shift 1 m). Ground height is fixed at {draft?.[2] ?? 0} m for this synthetic site.</p>
        </>
      )}
      {committed && draftDirty && (
        <p className="fine-print">Last evaluated position: E {committed[0]} m, N {committed[1]} m. <button type="button" className="text-action" onClick={ws.revertDraft}>Revert draft</button></p>
      )}
      {profile && state && (
        <>
          <Row label="Profile" value={`${profile.profile_id} · ${profile.species_size_label}`} />
          <Row label="State" value={`${caseState} · ${state.horizon_years} y · ${state.leaf_state}`} />
          <Row label="Crown" value={`radii ${state.crown_radii_m.join(' / ')} m at ${state.crown_center_height_m} m`} />
          <Row label="Trunk (derived)" value={`${state.trunk_height_m} m high · r ${state.trunk_radius_m} m`} />
          <Row label="Crown light" value={describeAttenuation(state.attenuation)} />
          <Row label="Upfront cost" value={`${formatPence(profile.cost_pence)} · ${profile.cost_scope}`} warn />
        </>
      )}
    </div>
  )
}

export function EvaluationControls({ ws }: { ws: Workspace }) {
  const job = ws.activeJob
  const described = job ? describeJob(job) : null
  const running = job ? job.status === 'queued' || job.status === 'running' : false
  const label = ws.busy === 'committing' ? 'Accepting revision…' : ws.busy === 'submitting' ? 'Submitting…' : ws.draftDirty ? 'Accept changes & evaluate' : 'Evaluate planting'
  return (
    <div className="detail-section">
      <span className="section-kicker">EVALUATION</span>
      <button type="button" className="primary-action" disabled={!ws.canEvaluate} onClick={() => void ws.evaluate()}>
        {label} <span aria-hidden="true">↗</span>
      </button>
      {running && (
        <button type="button" className="secondary-action" disabled={ws.busy === 'cancelling' || job?.cancel_requested} onClick={() => void ws.cancel()}>
          {job?.cancel_requested ? 'Cancel requested' : 'Cancel job'}
        </button>
      )}
      {ws.connection.status === 'connected' && !ws.connection.health.available_operations.includes('evaluate_layout') && (
        <p className="fine-print text-warning">This backend has no evaluate_layout provider, so no result can be computed.</p>
      )}
      <div role="status" aria-live="polite">
        {job && described && (
          <div className={`job-status tone-${described.tone}`}>
            <strong>{described.label}</strong>
            <span>Job {short(job.job_id, 8)} · scenario rev {job.scenario_revision}</span>
            <span>{described.detail}</span>
            {job.progress && job.progress.total > 0 && (
              <progress max={job.progress.total} value={job.progress.completed} aria-label="Job progress" />
            )}
            {running && !(job.progress && job.progress.total > 0) && (
              <>
                <progress aria-label="Job in progress; the backend reports no progress counts" data-testid="indeterminate-progress" />
                <span className="caption">The backend reports no progress counts, so no percentage or phase is estimated.</span>
              </>
            )}
          </div>
        )}
        {ws.notice && <p className="fine-print">{ws.notice}</p>}
      </div>
      {ws.error && <p className="error-box" role="alert">{ws.error}</p>}
    </div>
  )
}

const CURRENTNESS_TONE: Record<Currentness, string> = { current: 'tone-success', 'stale-draft': 'tone-warning', 'not-selected': 'tone-warning', superseded: 'tone-muted' }

export function ResultCard({ ws }: { ws: Workspace }) {
  const evaluations = ws.runs.filter(r => r.job.operation === 'evaluate_layout')
  const record = evaluations.find(r => r.result) ?? null
  const latestFailure = evaluations[0] && !evaluations[0].result ? evaluations[0] : null
  const primaryCase = ws.scenario?.input.objective.primary_case_id ?? null
  if (!record?.result) {
    return (
      <div className="detail-section result-section">
        <span className="section-kicker">CURRENT RESULT</span>
        <div className="empty-visual" aria-hidden="true"><span>—</span></div>
        <h3>{latestFailure ? `No result: job ${latestFailure.job.status}` : 'No calculation yet'}</h3>
        <p className="fine-print">{latestFailure ? describeJob(latestFailure.job).detail : 'Run an evaluation to compute the additional shade on the target from the backend evaluator.'}</p>
      </div>
    )
  }
  const result = record.result
  const currentness = ws.currentness(result)
  const failureNewer = latestFailure !== null && evaluations.indexOf(latestFailure) < evaluations.indexOf(record)
  return (
    <div className={`detail-section result-section result-${currentness}`}>
      <span className="section-kicker">{currentness === 'current' ? 'CURRENT RESULT' : 'LAST RESULT — NOT CURRENT'}</span>
      <ResultBody result={result} currentness={currentness} primaryCase={primaryCase} />
      {failureNewer && latestFailure && <p className="error-box">A later job {latestFailure.job.status}: {describeJob(latestFailure.job).detail}</p>}
    </div>
  )
}

function constraintSummary(result: Result) {
  if (result.constraints.length === 0) return 'none reported'
  const counts = { pass: 0, fail: 0, unknown: 0 }
  result.constraints.forEach(c => { counts[c.status] += 1 })
  return (['fail', 'unknown', 'pass'] as const).filter(k => counts[k]).map(k => `${counts[k]} ${k}`).join(' · ')
}

function ResultBody({ result, currentness, primaryCase }: { result: Result; currentness: Currentness; primaryCase: string | null }) {
  const metric = primaryMetric(result, primaryCase)
  const layout = result.layouts[0]
  const zero = metric?.value === 0
  return (
    <>
      <div className={`currentness ${CURRENTNESS_TONE[currentness]}`}>
        <strong>{CURRENTNESS_LABEL[currentness].label}</strong>
        <span>{CURRENTNESS_LABEL[currentness].detail}</span>
      </div>
      {metric ? (
        <div className={`metric${currentness !== 'current' ? ' metric-stale' : ''}`}>
          <span className="metric-value" data-testid="metric-value">{formatValue(metric.value)}</span>
          <span className="metric-unit">{unitLabel(metric.unit)}</span>
          <span className="metric-label">{metric.metric_id.replace(/_/g, ' ')} · {metric.quantity_kind} · case {metric.case_id} · {metric.horizon_years} y{metric.target_id ? ` · target ${metric.target_id}` : ''}</span>
          {zero && <span className="metric-note">Valid zero: the evaluator found no additional shade on the target for this placement and time bin.</span>}
        </div>
      ) : (
        <p className="fine-print text-warning">The result contains no metric.</p>
      )}
      {result.missing_metrics.length > 0 && <p className="fine-print text-warning">Missing: {result.missing_metrics.map(m => `${m.metric_id} (${m.reason})`).join('; ')}</p>}
      <div className="evidence-grid">
        <Row label="Mode" value={EXECUTION_MODE_LABEL[result.provenance.execution_mode]} warn={result.provenance.execution_mode !== 'live'} />
        <Row label="Run" value={short(result.run_id, 12)} />
        <Row label="Scenario rev" value={`${result.scenario_revision} (${result.scope})`} />
        {layout && <Row label="Layout" value={`${layout.layout.layout_id} rev ${layout.layout.revision} · ${layout.tree_count} tree`} />}
        {layout && <Row label="Placement" value={layout.layout.placements.map(p => `E ${p.position_enu_m[0]}, N ${p.position_enu_m[1]}`).join('; ')} />}
        {layout && <Row label="Cost" value={`${formatPence(layout.cost_pence)} upfront`} />}
        {layout && <Row label="Feasibility" value={layout.feasibility.replace('_', ' ')} warn={layout.feasibility !== 'feasible'} />}
        <Row label="Constraints" value={constraintSummary(result)} warn={result.constraints.length === 0 || result.constraints.some(c => c.status !== 'pass')} />
        <Row label="Evaluator" value={`${result.provenance.evaluator_version} · solar ${result.provenance.solar_version}`} />
        <Row label="Computed" value={`${result.provenance.compute_finished_at_utc.replace('T', ' ').replace(/\.\d+/, '')}`} />
        <Row label="Source hashes" value={`${Object.keys(result.provenance.source_hashes).length} bound`} />
        <Row label="Fingerprint" value={short(result.input_fingerprint, 12)} />
      </div>
      <details className="evidence-details">
        <summary>Constraints, assumptions &amp; limitations ({result.constraints.length + result.assumptions.length + result.limitations.length})</summary>
        {result.constraints.length > 0 && <ul>{result.constraints.map((c, i) => <li key={`c-${i}`} className={c.status === 'pass' ? undefined : 'text-warning'}>Constraint {c.rule}: {c.status}{c.observed_value !== null ? ` (observed ${c.observed_value}${c.unit ? ` ${c.unit}` : ''}${c.limit !== null ? `, limit ${c.limit}` : ''})` : ''}</li>)}</ul>}
        <ul>{result.assumptions.map(a => <li key={`a-${a}`}>{a}</li>)}{result.limitations.map(l => <li key={`l-${l}`} className="text-warning">{l}</li>)}</ul>
      </details>
    </>
  )
}

export function RunHistory({ ws }: { ws: Workspace }) {
  if (ws.runs.length < 2) return null
  return (
    <div className="detail-section">
      <span className="section-kicker">RUN HISTORY</span>
      <ol className="run-history">
        {ws.runs.map((r: RunRecord) => {
          const m = r.result ? primaryMetric(r.result, ws.scenario?.input.objective.primary_case_id ?? null) : null
          const c = r.result ? ws.currentness(r.result) : null
          return (
            <li key={r.job.job_id}>
              <span>rev {r.job.scenario_revision}{r.job.operation !== 'evaluate_layout' ? ` · ${r.job.operation.replace('_layouts', '').replace('_', ' ')}` : ''}</span>
              <strong>{m ? `${formatValue(m.value)} ${unitLabel(m.unit)}` : r.job.status}</strong>
              <em className={c ? CURRENTNESS_TONE[c] : 'tone-danger'}>{c ? CURRENTNESS_LABEL[c].label : r.job.error?.code ?? r.job.status.toUpperCase()}</em>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

export const positionKey = (p: Vec3 | null) => (p ? p.join(',') : '')
