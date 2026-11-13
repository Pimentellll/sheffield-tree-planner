import { useState } from 'react'
import { EXECUTION_MODE_LABEL, CURRENTNESS_LABEL, formatPence, formatValue, primaryMetric, unitLabel } from '../planning/evaluation'
import { exportGate, positionLabel, reviewPack, surveyView } from '../planning/report'
import type { Workspace } from '../planning/useWorkspace'

/** STP-028: rights-aware, provenance-linked proposal review pack. */
export default function ReportScreen({ ws }: { ws: Workspace }) {
  const [backendReply, setBackendReply] = useState<string | null>(null)
  const [exported, setExported] = useState<string | null>(null)
  if (ws.connection.status !== 'connected' || !ws.site || !ws.scenario || !ws.layout || !ws.profile) {
    return <section className="future-screen"><h1>Report<span className="heading-dot">.</span></h1><p>Connect the local backend to assemble a review pack from stored results.</p></section>
  }
  const { site, scenario, layout, profile } = ws
  const record = ws.runs.find(r => r.result?.operation === 'evaluate_layout') ?? null
  const result = record?.result ?? null
  const currentness = result ? ws.currentness(result) : null
  const gate = exportGate(site, result, currentness)
  const survey = surveyView(site, scenario)
  const metric = result ? primaryMetric(result, scenario.input.objective.primary_case_id) : null
  const synthetic = site.site_kind === 'synthetic_test'
  const apiVersion = ws.connection.health.version

  const download = () => {
    if (!gate.allowed || !result) return
    const pack = reviewPack({ site, scenario, layout, profile, result, nowIso: new Date().toISOString(), apiVersion })
    const text = JSON.stringify(pack, null, 2)
    const name = `canopy-review-${site.site_id}-rev${scenario.revision}-${result.run_id.slice(0, 8)}.json`
    const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }))
    const a = document.createElement('a')
    a.href = url
    a.download = name
    a.click()
    URL.revokeObjectURL(url)
    setExported(`${name} · ${text.length.toLocaleString('en-GB')} bytes`)
  }

  const askBackend = async () => {
    if (!result) return
    setBackendReply(null)
    try {
      const response = await fetch('/api/v1/operations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Canopy-Scenario-Id': scenario.scenario_id, 'X-Canopy-Scenario-Revision': String(scenario.revision) },
        body: JSON.stringify({ request_id: `ui-proposal-${Date.now()}`, operation: 'prepare_proposal', arguments: { result_refs: [{ run_id: result.run_id }] } }),
      })
      const body = await response.json()
      setBackendReply(response.ok ? `HTTP ${response.status}: proposal prepared (${JSON.stringify(body).slice(0, 200)}…)` : `HTTP ${response.status} ${body.code}: ${body.message}`)
    } catch (err) {
      setBackendReply(err instanceof Error ? err.message : String(err))
    }
  }

  return (
    <>
      <div className="page-heading no-print"><div><h1>Review pack<span className="heading-dot">.</span></h1><p>Everything a reviewer needs to check the proposal: the number, where it came from, what it does not cover, and who must still survey the site.</p></div><span className="pill pill-muted">STP-028</span></div>
      <div className="report">
      <article className="report-sheet" aria-labelledby="report-title">
        <header className="report-head">
          <span className="section-kicker">{synthetic ? 'SYNTHETIC TEST SITE · NOT SHEFFIELD · NOT A PLANTING PROPOSAL' : 'PROPOSAL FOR REVIEW · NOT PLANTING PERMISSION'}</span>
          <h2 id="report-title">{site.name}</h2>
          <p>Accepted scenario {scenario.scenario_id.slice(0, 8)}… revision {scenario.revision} · generated from stored backend records · CANOPY API {apiVersion}</p>
        </header>

        <section className="report-block" aria-labelledby="r-result">
          <h3 id="r-result">1. Result</h3>
          {!result ? <p>No evaluation has been run. Nothing to report.</p> : (
            <>
              <p className={`report-status ${currentness === 'current' ? 'tone-success' : 'tone-warning'}`} data-testid="report-currentness"><strong>{CURRENTNESS_LABEL[currentness!].label}</strong> {CURRENTNESS_LABEL[currentness!].detail}</p>
              {metric && <p className="report-metric"><strong data-testid="report-metric">{formatValue(metric.value)} {unitLabel(metric.unit)}</strong> {metric.metric_id.replace(/_/g, ' ')} ({metric.quantity_kind}) on {metric.target_id ?? 'all targets'}, case {metric.case_id}, {metric.horizon_years}-year tree state.</p>}
              <p className="fine-print">This is direct geometric shade for the declared time bin only. It is not cooling, energy, air-quality, carbon or flood benefit.</p>
              <dl className="chain report-chain">
                <dt>Run</dt><dd>{result.run_id} · {EXECUTION_MODE_LABEL[result.provenance.execution_mode]}</dd>
                <dt>Metric instance</dt><dd>{metric?.metric_instance_id ?? '—'}</dd>
                <dt>Job / request</dt><dd>{result.source_job_id} / {record?.job.request_id}</dd>
                <dt>Input fingerprint</dt><dd>{result.input_fingerprint}</dd>
                <dt>Evaluator</dt><dd>{result.provenance.evaluator_version} · solar {result.provenance.solar_version} · tool {result.provenance.tool_version}</dd>
                <dt>Computed</dt><dd>{result.provenance.compute_finished_at_utc}</dd>
                <dt>Source hashes</dt><dd>{Object.keys(result.provenance.source_hashes).length} bound to this run</dd>
                <dt>Feasibility</dt><dd>{result.layouts[0]?.feasibility.replace('_', ' ') ?? '—'}; constraints {result.constraints.map(c => `${c.rule}: ${c.status}`).join(', ') || 'none reported'}</dd>
              </dl>
            </>
          )}
        </section>

        <section className="report-block" aria-labelledby="r-layout">
          <h3 id="r-layout">2. Proposed planting</h3>
          <table className="layout-table">
            <thead><tr><th scope="col">Placement</th><th scope="col">Position (ENU m)</th><th scope="col">Geographic</th><th scope="col">Profile · cost</th></tr></thead>
            <tbody>
              {layout.placements.map(p => {
                const geo = positionLabel(site, p.position_enu_m)
                return (
                  <tr key={p.placement_id}>
                    <th scope="row">{p.placement_id}</th>
                    <td>E {p.position_enu_m[0]} · N {p.position_enu_m[1]} · U {p.position_enu_m[2]}</td>
                    <td data-testid="geo-label">{geo.kind === 'enu-only' ? <em>{geo.reason}</em> : <>≈ {geo.latitude.toFixed(6)}, {geo.longitude.toFixed(6)}<small>{geo.reason}</small></>}</td>
                    <td>{profile.profile_id} · {formatPence(profile.cost_pence)}<small>{profile.cost_scope} ({profile.price_date})</small></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <p className="fine-print">ENU positions are metres east, north and up from the SiteBundle origin in the analysis frame ({site.analysis_frame}); they are not latitude/longitude or OS grid coordinates. Budget: {formatPence(scenario.input.constraints.budget_pence)} {scenario.input.constraints.budget_basis}.</p>
        </section>

        <section className="report-block" aria-labelledby="r-survey">
          <h3 id="r-survey">3. Still required before planting</h3>
          {survey.recorded.length > 0
            ? <ul>{survey.recorded.map(s => <li key={s}>{s}</li>)}</ul>
            : <p className="fine-print" data-testid="survey-none">No survey requirement is recorded in this scenario or SiteBundle. That does not mean none apply:</p>}
          <ul>{survey.standing.map(s => <li key={s}>{s}</li>)}</ul>
          {(survey.blockers.length > 0 || survey.warnings.length > 0) && <ul>{[...survey.blockers, ...survey.warnings].map(s => <li key={s} className="text-warning">{s}</li>)}</ul>}
          {survey.coverageLimits.length > 0 && <><p className="fine-print">Coverage limitations:</p><ul>{survey.coverageLimits.map(s => <li key={s}>{s}</li>)}</ul></>}
        </section>

        <section className="report-block" aria-labelledby="r-assume">
          <h3 id="r-assume">4. Assumptions and limitations</h3>
          <ul>
            {scenario.input.assumptions.map(a => <li key={`s-${a}`}>{a}</li>)}
            {result?.limitations.map(l => <li key={`l-${l}`} className="text-warning">{l}</li>)}
          </ul>
        </section>

        <section className="report-block" aria-labelledby="r-rights">
          <h3 id="r-rights">5. Sources and rights</h3>
          <table className="layout-table">
            <thead><tr><th scope="col">Source</th><th scope="col">Local</th><th scope="col">Team</th><th scope="col">Public</th><th scope="col">Export</th></tr></thead>
            <tbody>
              {site.rights.map(r => (
                <tr key={r.source_id}>
                  <th scope="row">{r.source_reference}<small>{r.licence_reference}</small><small>Attribution: {r.required_attribution}</small></th>
                  {[r.local_use_status, r.team_share_status, r.public_display_status, r.export_status].map((v, i) => <td key={i} className={v === 'permitted' ? 'text-ok' : 'text-warning'}>{v}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </article>

      <aside className="detail-panel report-actions no-print" aria-label="Export">
        <div className="detail-section">
          <span className="section-kicker">EXPORT</span>
          <button type="button" className="primary-action" disabled={!gate.allowed} onClick={download}>Download review pack (JSON) <span aria-hidden="true">↓</span></button>
          <button type="button" className="secondary-action" disabled={!gate.allowed} onClick={() => window.print()}>Print / save as PDF</button>
          {!gate.allowed && <ul className="fine-print text-warning" data-testid="export-blocked">{gate.reasons.map(r => <li key={r}>{r}</li>)}</ul>}
          {exported && <p className="fine-print" data-testid="export-done">Saved {exported}. It contains the stored records unchanged plus the labels above.</p>}
          <p className="fine-print">Assembled in the browser from stored records: the backend has no approved export handler yet.</p>
          <button type="button" className="text-action" onClick={() => void askBackend()} disabled={!result}>Ask the backend to prepare a proposal</button>
          {backendReply && <p className="fine-print" data-testid="backend-proposal">{backendReply}</p>}
        </div>
      </aside>
      </div>
    </>
  )
}
