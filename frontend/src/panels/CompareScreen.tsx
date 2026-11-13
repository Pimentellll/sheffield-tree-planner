import { useMemo, useState } from 'react'
import type { JobRequest, Result, Scenario, TreeState, Vec3 } from '../api/types'
import type { SceneData } from '../api/session'
import type { CandidateMarker } from '../scene/SiteScene'
import SiteScene from '../scene/SiteScene'
import {
  CASE_ROLE_LABEL, SUPPORTED_METRICS, compareRuns, deltaRows, timeBins, winterView,
} from '../planning/comparison'
import { CURRENTNESS_LABEL, EXECUTION_MODE_LABEL, describeValue, formatPence, formatValue, unitLabel } from '../planning/evaluation'
import type { RunRecord, Workspace } from '../planning/useWorkspace'

type Stored = RunRecord & { readonly result: Result; readonly inputScenario: Scenario }
const stored = (ws: Workspace, op: Result['operation']) =>
  ws.runs.filter((r): r is Stored => r.result?.operation === op && r.inputScenario !== null)
const runLabel = (r: Stored) => {
  const p = r.result.layouts[0]?.layout.placements[0]?.position_enu_m
  const m = r.result.metrics[0]
  return `rev ${r.result.scenario_revision} · ${p ? `E ${p[0]}, N ${p[1]}` : 'no placement'} · ${m ? `${formatValue(m.value)} ${unitLabel(m.unit)}` : 'no metric'} · ${r.result.run_id.slice(0, 8)}`
}
const signed = (v: number) => (v > 0 ? `+${formatValue(v)}` : v < 0 ? `−${formatValue(-v)}` : '0')

export default function CompareScreen({ ws, scene, candidates, treeState }: { ws: Workspace; scene: SceneData | null; candidates: readonly CandidateMarker[]; treeState: TreeState | null }) {
  if (ws.connection.status !== 'connected' || !ws.scenario) {
    return <section className="future-screen"><h1>Compare<span className="heading-dot">.</span></h1><p>Connect the local backend to compare stored runs.</p></section>
  }
  return (
    <>
      <div className="page-heading"><div><h1>Compare &amp; evidence<span className="heading-dot">.</span></h1><p>Analysis cases, controlled comparisons of stored runs, and the evidence behind every number.</p></div><span className="pill pill-muted">STP-025</span></div>
      <div className="notice" role="note"><span className="notice-icon" aria-hidden="true">ⓘ</span><div><strong>Scope of what is computed</strong><p>This system computes direct geometric shade metrics only ({SUPPORTED_METRICS.join(', ')}). It does not compute temperature, air quality, CO₂, flood or energy-bill savings, and none are shown.</p></div></div>
      <div className="compare-grid">
        <RunComparison ws={ws} scene={scene} candidates={candidates} treeState={treeState} />
        <div className="compare-side">
          <CasesPanel ws={ws} />
          <WinterPanel ws={ws} />
          <BackendComparison ws={ws} />
          <EvidencePanel ws={ws} />
        </div>
      </div>
    </>
  )
}

function CasesPanel({ ws }: { ws: Workspace }) {
  const scenario = ws.scenario!
  const cases = scenario.input.evaluation_cases
  const [selected, setSelected] = useState(scenario.input.objective.primary_case_id)
  const current = cases.find(c => c.case_id === selected) ?? cases[0]
  const evaluations = stored(ws, 'evaluate_layout')
  const latest = evaluations[0]?.result ?? null
  const metrics = latest ? latest.metrics.filter(m => m.case_id === current?.case_id) : []
  const missing = latest ? latest.missing_metrics.filter(m => m.case_id === current?.case_id) : []
  return (
    <section className="detail-panel compare-card" aria-labelledby="cases-heading">
      <div className="detail-section">
        <span className="section-kicker">ANALYSIS CASES · SEASON</span>
        <h2 id="cases-heading" className="card-title">Evaluated cases</h2>
        <div role="radiogroup" aria-label="Analysis case" className="case-list">
          {cases.map(c => (
            <label key={c.case_id} className={`case-option${c.case_id === current?.case_id ? ' active' : ''}`}>
              <input type="radio" name="case" value={c.case_id} checked={c.case_id === current?.case_id} onChange={() => setSelected(c.case_id)} />
              <span><strong>{c.case_id}</strong> · {CASE_ROLE_LABEL[c.role]}{c.case_id === scenario.input.objective.primary_case_id ? ' · primary' : ''}</span>
            </label>
          ))}
        </div>
        {current && (
          <>
            <div className="readiness-row"><span>Tree state</span><strong>{current.profile_state} · {current.horizon_years} y</strong></div>
            <div className="readiness-row"><span>Targets</span><strong>{current.target_ids.map(t => `${t} ×${current.target_weights[t] ?? '—'}`).join(', ')}</strong></div>
            <div className="readiness-row"><span>Area basis</span><strong>{current.area_basis}</strong></div>
            <div className="readiness-row"><span>Weather</span><strong>{current.weather_ref ?? 'none (geometric)'}</strong></div>
            <ul className="bin-list" aria-label="Time bins">
              {timeBins(current, scenario.input.display_time_zone).map(b => <li key={b.utc}><code>{b.utc}</code> UTC · {b.local} ({b.zone}) · {b.durationH} h</li>)}
            </ul>
            <p className="fine-print">These are the analysis bins the evaluator integrates. The 3D view does not animate the sun and there is no view-only time slider, so nothing on screen implies a different time was analysed.</p>
            <span className="fine-label">Latest evaluation for this case</span>
            {!latest ? <p className="fine-print">No stored evaluation yet.</p> : metrics.length === 0 && missing.length === 0
              ? <p className="fine-print">The latest run (rev {latest.scenario_revision}) has no metric for this case.</p>
              : <ul className="bin-list">
                  {metrics.map(m => <li key={m.metric_instance_id}><strong>{formatValue(m.value)} {unitLabel(m.unit)}</strong> {m.metric_id.replace(/_/g, ' ')} · {m.quantity_kind}{m.target_id ? ` · ${m.target_id}` : ''}</li>)}
                  {missing.map(m => <li key={m.metric_id} className="text-warning">{m.metric_id}: not computed — {m.reason}</li>)}
                </ul>}
          </>
        )}
      </div>
    </section>
  )
}

function WinterPanel({ ws }: { ws: Workspace }) {
  const latest = stored(ws, 'evaluate_layout')[0]?.result ?? null
  const view = winterView(ws.scenario!, latest)
  return (
    <section className="detail-panel compare-card" aria-labelledby="winter-heading">
      <div className="detail-section">
        <span className="section-kicker">WINTER TRADE-OFF</span>
        <h2 id="winter-heading" className="card-title">Winter sun</h2>
        {view.status === 'not-in-scenario' && <p className="fine-print" data-testid="winter-status">Not evaluated: the accepted scenario has no winter-check case and no winter limit. This is not a finding of zero winter sun loss.</p>}
        {view.status === 'no-result' && <p className="fine-print" data-testid="winter-status">Winter case(s) {view.cases.map(c => c.case_id).join(', ')} are defined but no stored evaluation exists yet.</p>}
        {view.status === 'reported' && (
          <ul className="bin-list" data-testid="winter-status">
            {view.limits.map(l => <li key={`l-${l.case_id}-${l.target_id}`}>Limit: {l.case_id}{l.target_id ? ` / ${l.target_id}` : ''} ≤ {l.maximum_loss_m2_h} m²·h</li>)}
            {view.metrics.map(m => <li key={m.metric_instance_id}><strong>{formatValue(m.value)} {unitLabel(m.unit)}</strong> {m.metric_id.replace(/_/g, ' ')} · {m.case_id}</li>)}
            {view.constraints.map((c, i) => <li key={`c-${i}`} className={c.status === 'pass' ? undefined : 'text-warning'}>{c.rule}: {c.status}</li>)}
            {view.missing.map(m => <li key={`m-${m.metric_id}-${m.case_id}`} className="text-warning">{m.metric_id} ({m.case_id}): not computed — {m.reason}</li>)}
          </ul>
        )}
      </div>
    </section>
  )
}

/** Side-by-side comparison of two stored evaluate runs; differences are arithmetic on returned values only. */
function RunComparison({ ws, scene, candidates, treeState }: { ws: Workspace; scene: SceneData | null; candidates: readonly CandidateMarker[]; treeState: TreeState | null }) {
  const runs = stored(ws, 'evaluate_layout')
  const [baseId, setBaseId] = useState<string | null>(null)
  const [altId, setAltId] = useState<string | null>(null)
  const alt = runs.find(r => r.result.run_id === altId) ?? runs[0] ?? null
  const base = runs.find(r => r.result.run_id === baseId) ?? runs.find(r => r !== alt) ?? null
  const comparison = useMemo(() => (base && alt && base !== alt ? compareRuns({ result: base.result, scenario: base.inputScenario }, { result: alt.result, scenario: alt.inputScenario }) : null), [base, alt])
  const at = (r: Stored | null) => (r?.result.layouts[0]?.layout.placements[0]?.position_enu_m as Vec3 | undefined) ?? null
  return (
    <section className="site-panel" aria-labelledby="cmp-heading">
      <div className="panel-head"><div><span className="section-kicker">CONTROLLED COMPARISON</span><h2 id="cmp-heading">Two stored runs</h2></div><span className="tiny-tag">{runs.length} STORED</span></div>
      {runs.length < 2 ? (
        <div className="detail-section compare-empty"><p>At least two stored evaluations are needed. Evaluate, move the tree, then evaluate again in the Planning studio.</p></div>
      ) : (
        <>
          <SiteScene scene={scene} candidates={candidates.map(c => ({ ...c, selected: false }))} treeState={treeState} committed={at(base)} draft={at(alt)} editable={false} onDraftChange={() => {}} siteLabel="BASE (GHOST) VS ALTERNATIVE" />
          <div className="detail-section cmp-body">
            <div className="field-grid">
              <label className="select-field"><span>Base</span>
                <select aria-label="Base run" value={base?.result.run_id ?? ''} onChange={e => setBaseId(e.target.value)}>
                  {runs.map(r => <option key={r.result.run_id} value={r.result.run_id}>{runLabel(r)}</option>)}
                </select>
              </label>
              <label className="select-field"><span>Alternative</span>
                <select aria-label="Alternative run" value={alt?.result.run_id ?? ''} onChange={e => setAltId(e.target.value)}>
                  {runs.map(r => <option key={r.result.run_id} value={r.result.run_id}>{runLabel(r)}</option>)}
                </select>
              </label>
            </div>
            {!comparison ? <p className="fine-print">Choose two different runs.</p> : (
              <>
                <p className="cmp-kind" data-testid="comparison-kind">
                  {comparison.kind === 'controlled-relocation' ? 'Controlled relocation: one placement moved, every other input identical.'
                    : comparison.kind === 'identical-inputs' ? 'Identical inputs: any difference would indicate non-determinism.'
                      : 'Not a controlled comparison: more than one input changed (listed below).'}
                </p>
                <table className="layout-table" data-testid="comparison-table">
                  <caption className="sr-only">Metrics of the base and alternative runs</caption>
                  <thead><tr><th scope="col">Metric</th><th scope="col">Base</th><th scope="col">Alternative</th><th scope="col">Δ (alt − base)</th></tr></thead>
                  <tbody>
                    {comparison.pairs.map(p => (
                      <tr key={p.key}>
                        <th scope="row">{p.label}</th>
                        <td>{p.base ? `${formatValue(p.base.value)} ${unitLabel(p.base.unit)}` : '—'}</td>
                        <td>{p.alternative ? `${formatValue(p.alternative.value)} ${unitLabel(p.alternative.unit)}` : '—'}</td>
                        <td>{p.difference !== null ? <strong>{signed(p.difference)}</strong> : <em>{p.note}</em>}</td>
                      </tr>
                    ))}
                    <tr><th scope="row">Upfront cost</th><td>{formatPence(base!.result.layouts[0]?.cost_pence ?? 0)}</td><td>{formatPence(alt!.result.layouts[0]?.cost_pence ?? 0)}</td><td>—</td></tr>
                  </tbody>
                </table>
                <div className="butterfly" aria-hidden="true">
                  <div className="butterfly-head"><span>BASE</span><span>ALTERNATIVE</span></div>
                  {comparison.pairs.filter(p => p.base && p.alternative).map(p => {
                    const max = Math.max(Math.abs(p.base!.value), Math.abs(p.alternative!.value), 1e-9)
                    return (
                      <div key={p.key} className="butterfly-row">
                        <em>{formatValue(p.base!.value)}</em>
                        <div className="bar left"><i style={{ width: `${(Math.abs(p.base!.value) / max) * 100}%` }} /></div>
                        <span>{p.label}</span>
                        <div className="bar right"><i style={{ width: `${(Math.abs(p.alternative!.value) / max) * 100}%` }} /></div>
                        <em>{formatValue(p.alternative!.value)}</em>
                      </div>
                    )
                  })}
                </div>
                <p className="fine-print">Δ is the UI's subtraction of two stored backend values with identical metric, case, target, unit, kind and horizon; it is not a backend comparison result. Runs: base {base!.result.run_id.slice(0, 12)}… ({ws.currentness(base!.result) === 'current' ? 'current' : CURRENTNESS_LABEL[ws.currentness(base!.result)].label.toLowerCase()}), alternative {alt!.result.run_id.slice(0, 12)}… ({ws.currentness(alt!.result) === 'current' ? 'current' : CURRENTNESS_LABEL[ws.currentness(alt!.result)].label.toLowerCase()}).</p>
                <details className="evidence-details" open={comparison.changes.length > 0 && comparison.changes.length < 6}>
                  <summary>Changed inputs ({comparison.changes.length}) · moved placements ({comparison.movedPlacements.length})</summary>
                  <ul>
                    {comparison.movedPlacements.map(m => <li key={m.placementId}>{m.placementId}: {describeValue(m.from)} → {describeValue(m.to)} (ENU m)</li>)}
                    {comparison.changes.map(c => <li key={c.path}><code>{c.path}</code>: {describeValue(c.before)} → {describeValue(c.after)}</li>)}
                  </ul>
                </details>
              </>
            )}
          </div>
        </>
      )}
    </section>
  )
}

const compareLocationRequest = (position: Vec3, placementId: string) => (head: Scenario, requestId: string): JobRequest => ({
  request_id: requestId,
  operation: 'compare_locations',
  scenario_ref: { scenario_id: head.scenario_id, revision: head.revision, scope: head.scope },
  arguments: { layout_ref: head.input.proposed_layout_ref!, placement_id: placementId, alternative_position_enu_m: position },
})

/** Backend controlled comparison (compare_locations); rendered only from a returned ComparisonMetadata. */
function BackendComparison({ ws }: { ws: Workspace }) {
  const available = ws.connection.status === 'connected' && ws.connection.health.available_operations.includes('compare_locations')
  const record = ws.runs.find(r => r.result?.operation === 'compare_locations' || r.result?.operation === 'compare_scenarios') ?? null
  const rows = record?.result ? deltaRows(record.result) : []
  return (
    <section className="detail-panel compare-card" aria-labelledby="backend-cmp-heading">
      <div className="detail-section">
        <span className="section-kicker">BACKEND COMPARISON</span>
        <h2 id="backend-cmp-heading" className="card-title">Relocate one tree (server-side)</h2>
        <p className="fine-print">Asks the backend to evaluate the draft position against the accepted placement with every other input fixed.</p>
        <button type="button" className="secondary-action" disabled={!available || !ws.draftPosition || !ws.placementId || ws.busy !== null}
          onClick={() => ws.draftPosition && ws.placementId && void ws.submit(compareLocationRequest(ws.draftPosition, ws.placementId))}>
          Compare draft position on the backend
        </button>
        {ws.activeJob && ws.activeJob.operation.startsWith('compare') && (
          <p className="fine-print" role="status" data-testid="compare-job">Job {ws.activeJob.job_id.slice(0, 8)}… {ws.activeJob.operation}: <strong>{ws.activeJob.status}</strong>{ws.activeJob.error ? ` — ${ws.activeJob.error.code}: ${ws.activeJob.error.message}` : ''}</p>
        )}
        {record?.result && <p className="fine-print">Run {record.result.run_id.slice(0, 12)}… · {record.result.operation} · scenario rev {record.result.scenario_revision} · {CURRENTNESS_LABEL[ws.currentness(record.result)].label}</p>}
        {ws.error && <p className="error-box" role="alert">{ws.error}</p>}
        {!available && <p className="fine-print text-warning" data-testid="compare-unavailable">No compare_locations provider is registered on this backend, so no server comparison can run. The stored-run comparison is the only comparison shown.</p>}
        {record?.result?.comparison && (
          <ul className="bin-list">
            <li>Mode: {record.result.comparison.mode} · changed: {record.result.comparison.changed_inputs.join(', ') || 'none listed'}</li>
            {rows.map((r, i) => (
              <li key={i} className={r.resolved ? undefined : 'text-warning'} data-testid="backend-delta">
                <strong>{r.base ? `${r.base.metric_id.replace(/_/g, ' ')} · ${r.base.case_id}${r.base.target_id ? ` · ${r.base.target_id}` : ''}` : 'unresolved metric'}</strong>{' '}
                {r.base ? `${formatValue(r.base.value)} → ${r.alternative ? formatValue(r.alternative.value) : '?'}` : ''} · Δ {signed(r.delta.value)} {unitLabel(r.delta.unit)}
                {r.base?.layout_id ? <small className="delta-layout"> layout {r.base.layout_id.length > 18 ? `…${r.base.layout_id.slice(-12)}` : r.base.layout_id}</small> : null}
                {r.resolved ? '' : ' (metric instance not found in result)'}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

/** Evidence chain for each stored result, and what is not available (agent narrative). */
function EvidencePanel({ ws }: { ws: Workspace }) {
  const results = ws.runs.filter((r): r is RunRecord & { result: Result } => r.result !== null)
  const [open, setOpen] = useState<string | null>(null)
  return (
    <section className="detail-panel compare-card" aria-labelledby="evidence-heading">
      <div className="detail-section">
        <span className="section-kicker">EVIDENCE</span>
        <h2 id="evidence-heading" className="card-title">Where each number came from</h2>
        <p className="fine-print" data-testid="agent-status">Agent tool history and narrative: not available. This backend exposes no planning-agent endpoint yet (STP-019/022), so no agent explanation is shown. Jobs below list their request ids; agent-submitted jobs would appear here as ordinary stored jobs.</p>
        {ws.runs.length === 0 && <p className="fine-print">No stored jobs yet.</p>}
        <ol className="evidence-chain">
          {ws.runs.map(r => (
            <li key={r.job.job_id}>
              <button type="button" className="text-action" aria-expanded={open === r.job.job_id} onClick={() => setOpen(open === r.job.job_id ? null : r.job.job_id)}>
                {r.job.operation} · rev {r.job.scenario_revision} · {r.job.status}{r.result ? ` · ${CURRENTNESS_LABEL[ws.currentness(r.result)].label}` : ''}
              </button>
              {open === r.job.job_id && (
                <dl className="chain">
                  <dt>Request</dt><dd>{r.job.request_id}</dd>
                  <dt>Job</dt><dd>{r.job.job_id} · created {r.job.created_at_utc}</dd>
                  <dt>Input fingerprint</dt><dd>{r.job.input_fingerprint}</dd>
                  {r.job.error && <><dt>Error</dt><dd className="text-warning">{r.job.error.code}: {r.job.error.message}</dd></>}
                  {r.result && <>
                    <dt>Run</dt><dd>{r.result.run_id} · {EXECUTION_MODE_LABEL[r.result.provenance.execution_mode]}</dd>
                    <dt>Scenario snapshot</dt><dd>{r.result.input_snapshot_ref.scenario_id} rev {r.result.input_snapshot_ref.revision} ({r.result.input_snapshot_ref.scope})</dd>
                    <dt>Metrics</dt><dd>{r.result.metrics.map(m => `${m.metric_instance_id.slice(0, 10)}…: ${formatValue(m.value)} ${unitLabel(m.unit)} (${m.metric_id}, ${m.case_id})`).join('; ') || 'none'}</dd>
                    <dt>Code &amp; versions</dt><dd>evaluator {r.result.provenance.evaluator_version} · solar {r.result.provenance.solar_version} · search {r.result.provenance.search_version} · tool {r.result.provenance.tool_version} · schema {r.result.provenance.schema_version}</dd>
                    <dt>Devices</dt><dd>physics {r.result.provenance.physics_device ? `${r.result.provenance.physics_device.name} (${r.result.provenance.physics_device.backend})` : 'not recorded'} · inference {r.result.provenance.inference_device ? r.result.provenance.inference_device.name : 'none (no model involved)'}</dd>
                    <dt>Timings</dt><dd>{Object.entries(r.result.provenance.timings_s).map(([k, v]) => `${k} ${formatValue(v)} s`).join(' · ') || 'not recorded'}</dd>
                    <dt>Source hashes ({Object.keys(r.result.provenance.source_hashes).length})</dt>
                    <dd><ul>{Object.entries(r.result.provenance.source_hashes).map(([k, v]) => <li key={k}><code>{k}</code> {v.slice(0, 16)}…</li>)}</ul></dd>
                    <dt>Sources</dt><dd>{r.result.source_ids.join(', ') || 'none'}</dd>
                    <dt>Limitations</dt><dd>{r.result.limitations.join(' ') || 'none recorded'}</dd>
                  </>}
                </dl>
              )}
            </li>
          ))}
        </ol>
        {results.length > 0 && <p className="fine-print">Uncertainty: the evaluator reports no uncertainty range. Values are exact only for its declared synthetic inputs and the assumptions listed with each result.</p>}
      </div>
    </section>
  )
}
