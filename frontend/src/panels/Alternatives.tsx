import type { JobRequest, Scenario } from '../api/types'
import { ROLE_LABEL, layoutRows, objectiveView, outcomeView, spendText } from '../planning/alternatives'
import { CURRENTNESS_LABEL, formatPence, formatValue, unitLabel } from '../planning/evaluation'
import type { Workspace } from '../planning/useWorkspace'

const searchRequest = (head: Scenario, requestId: string): JobRequest => ({
  request_id: requestId,
  operation: 'search_layouts',
  scenario_ref: { scenario_id: head.scenario_id, revision: head.revision, scope: head.scope },
  arguments: {},
})

/** STP-018: run the registered search and show every evaluated layout it returned. */
export function AlternativesPanel({ ws, selectedLayoutId, onSelectLayout }: { ws: Workspace; selectedLayoutId: string | null; onSelectLayout: (id: string | null) => void }) {
  if (ws.connection.status !== 'connected' || !ws.scenario) return null
  const searchAvailable = ws.connection.health.available_operations.includes('search_layouts')
  const record = ws.runs.find(r => r.result?.operation === 'search_layouts') ?? null
  const failed = ws.runs.find(r => r.job.operation === 'search_layouts' && !r.result) ?? null
  const objective = objectiveView(ws.scenario)
  return (
    <div className="detail-section" data-testid="alternatives">
      <span className="section-kicker">PLANTING OPTIONS</span>
      <p className="fine-print">Objective (accepted rev {ws.scenario.revision}): {objective.text}{objective.target ? ` · target ${objective.target}` : ''}.</p>
      <button type="button" className="secondary-action" disabled={!searchAvailable || ws.busy !== null || ws.draftDirty} onClick={() => void ws.submit(searchRequest)}>
        Find planting options
      </button>
      {!searchAvailable && (
        <p className="fine-print text-warning" data-testid="search-unavailable">
          This backend has no registered search provider (available: {ws.connection.health.available_operations.join(', ') || 'none'}), so no options can be computed. Nothing is shown in their place.
        </p>
      )}
      {searchAvailable && ws.draftDirty && <p className="fine-print">Accept or discard your draft first; search runs on the accepted revision.</p>}
      {failed && (!record || ws.runs.indexOf(failed) < ws.runs.indexOf(record)) && (
        <p className="error-box">Latest search {failed.job.status}: {failed.job.error ? `${failed.job.error.code}: ${failed.job.error.message}` : 'no result stored'}.</p>
      )}
      {record?.result && <SearchResultView ws={ws} record={record} selectedLayoutId={selectedLayoutId} onSelectLayout={onSelectLayout} />}
    </div>
  )
}

function SearchResultView({ ws, record, selectedLayoutId, onSelectLayout }: { ws: Workspace; record: Workspace['runs'][number]; selectedLayoutId: string | null; onSelectLayout: (id: string | null) => void }) {
  const result = record.result!
  const outcome = outcomeView(result)
  const rows = layoutRows(result, record.inputScenario)
  const currentness = ws.currentness(result)
  return (
    <div className="search-result">
      <div className={`currentness tone-${currentness === 'current' ? 'success' : 'warning'}`}>
        <strong>{CURRENTNESS_LABEL[currentness].label}</strong>
        <span>Run {result.run_id.slice(0, 12)}… · scenario rev {result.scenario_revision} · {result.provenance.execution_mode} · search {result.provenance.search_version} seed {result.provenance.seed}</span>
      </div>
      <div className={`job-status tone-${outcome.tone}`} data-testid="search-outcome">
        <strong>{outcome.title}</strong>
        <span>{outcome.detail}</span>
      </div>
      {rows.length === 0 ? <p className="fine-print">The result contains no evaluated layouts.</p> : (
        <table className="layout-table">
          <caption className="sr-only">Evaluated layouts returned by the search</caption>
          <thead><tr><th scope="col">Layout</th><th scope="col">Shade</th><th scope="col">Spend · trees</th><th scope="col">Status</th></tr></thead>
          <tbody>
            {rows.map(row => (
              <tr key={`${row.layoutId}@${row.revision}`} className={selectedLayoutId === row.layoutId ? 'row-selected' : undefined}>
                <th scope="row">
                  <button type="button" className="text-action" aria-pressed={selectedLayoutId === row.layoutId} onClick={() => onSelectLayout(selectedLayoutId === row.layoutId ? null : row.layoutId)}>
                    {ROLE_LABEL[row.role]}{row.selected ? ' ★' : ''}
                  </button>
                  <small title={`${row.layoutId}@${row.revision}`}>{row.layoutId.length > 18 ? `…${row.layoutId.slice(-14)}` : row.layoutId}@{row.revision}</small>
                  <small>{row.placements.map(p => `E ${p.position_enu_m[0]}, N ${p.position_enu_m[1]}`).join(' · ')}</small>
                </th>
                <td>{row.metric ? <><strong>{formatValue(row.metric.value)}</strong> {unitLabel(row.metric.unit)}</> : <em>no metric</em>}</td>
                <td>{spendText(row, formatPence)}<small>{row.treeCount} tree{row.treeCount === 1 ? '' : 's'}{row.maxTreeCount !== null ? ` of max ${row.maxTreeCount}` : ''}</small></td>
                <td>
                  <span className={row.feasibility === 'feasible' ? 'text-ok' : 'text-warning'}>{row.feasibility.replace('_', ' ')}</span>
                  <small>{row.counts.fail ? `${row.counts.fail} fail · ` : ''}{row.counts.unknown ? `${row.counts.unknown} unknown · ` : ''}{row.counts.pass} pass</small>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <details className="evidence-details">
        <summary>Constraint explanations ({result.constraints.length})</summary>
        <ul>
          {rows.flatMap(row => [
            ...row.reasons.map(reason => <li key={`${row.layoutId}-r-${reason}`}>{row.layoutId}: {reason}</li>),
            ...row.constraints.map((c, i) => (
              <li key={`${row.layoutId}-c-${i}`} className={c.status === 'pass' ? undefined : 'text-warning'}>
                {row.layoutId} · {c.rule}: <strong>{c.status}</strong>
                {c.observed_value !== null ? ` (observed ${c.observed_value}${c.unit ? ` ${c.unit}` : ''}${c.limit !== null ? `, limit ${c.limit}` : ''})` : ''}
                {c.evidence.length ? ` — ${c.evidence.join('; ')}` : ''}
              </li>
            )),
          ])}
        </ul>
      </details>
      {result.limitations.length > 0 && <p className="fine-print text-warning">{result.limitations.join(' ')}</p>}
    </div>
  )
}
