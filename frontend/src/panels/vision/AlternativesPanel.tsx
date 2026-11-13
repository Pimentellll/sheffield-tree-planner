import type { JobRequest, Metric, Scenario } from '../../api/types'
import { objectiveView, outcomeView, spendText } from '../../planning/alternatives'
import {
  CURRENTNESS_PILL,
  FEASIBILITY_LABEL,
  FEASIBILITY_PILL,
  RANKING_UNAVAILABLE,
  bestCaptionApplies,
  bestLayoutCaption,
  latestSearch,
  layoutCards,
  noFeasibleLayout,
  pendingSearchText,
  scoreNote,
  searchAvailability,
  shadeNote,
} from '../../planning/alternativesView'
import type { LayoutCard } from '../../planning/alternativesView'
import { CURRENTNESS_LABEL, EXECUTION_MODE_LABEL, formatPence, formatValue, unitLabel } from '../../planning/evaluation'
import type { Workspace } from '../../planning/useWorkspace'
import './AlternativesPanel.css'

const searchRequest = (head: Scenario, requestId: string): JobRequest => ({
  request_id: requestId,
  operation: 'search_layouts',
  scenario_ref: { scenario_id: head.scenario_id, revision: head.revision, scope: head.scope },
  arguments: {},
})

type Props = { ws: Workspace; selectedLayoutId: string | null; onSelectLayout: (id: string | null) => void }

/**
 * C05 (Product Vision v2): the layouts one registered search evaluated. Only returned layouts are
 * shown, each with its stored cost and primary-case shade; nothing is ranked.
 */
export function AlternativesPanel({ ws, selectedLayoutId, onSelectLayout }: Props) {
  if (ws.connection.status !== 'connected' || !ws.scenario) return null
  const availability = searchAvailability(ws.connection.health.available_operations)
  const { record, pending, failure } = latestSearch(ws.runs, ws.activeJob)
  const objective = objectiveView(ws.scenario)
  return (
    <div className="detail-section c05" data-testid="alternatives">
      <span className="section-kicker">PLANTING OPTIONS</span>
      <p className="fine-print">Objective (accepted rev {ws.scenario.revision}): {objective.text}{objective.target ? ` · target ${objective.target}` : ''}.</p>
      <button type="button" className="secondary-action" disabled={!availability.available || ws.busy !== null || ws.draftDirty} onClick={() => void ws.submit(searchRequest)}>
        Find planting options
      </button>
      {!availability.available && (
        <p className="fine-print text-warning" data-testid="search-unavailable">
          Search is not offered by this backend (available: {availability.offered}), so no layouts can be computed. Nothing is shown in their place.
        </p>
      )}
      {availability.available && ws.draftDirty && <p className="fine-print">Accept or discard your draft first; search runs on the accepted revision.</p>}
      {pending && <p className={ws.jobStatusLost ? 'fine-print text-warning' : 'fine-print'}>{pendingSearchText(pending, ws.jobStatusLost)}</p>}
      {failure && (
        <p className="error-box">Latest search {failure.job.status}: {failure.job.error ? `${failure.job.error.code}: ${failure.job.error.message}` : 'no result stored'}.</p>
      )}
      {availability.available && !record && !pending && !failure && (
        <p className="fine-print">No search has run yet. A search evaluates whole layouts on the accepted revision.</p>
      )}
      {record?.result && <SearchResult ws={ws} record={record} selectedLayoutId={selectedLayoutId} onSelectLayout={onSelectLayout} />}
    </div>
  )
}

function SearchResult({ ws, record, selectedLayoutId, onSelectLayout }: Props & { record: Workspace['runs'][number] }) {
  const result = record.result!
  const outcome = outcomeView(result)
  const cards = layoutCards(result, record.inputScenario)
  const nothingFeasible = noFeasibleLayout(cards)
  const currentness = ws.currentness(result)
  const status = CURRENTNESS_LABEL[currentness]
  return (
    <div className="c05-result">
      <h3 className="section-title">
        Layouts from run <span className="mono" title={result.run_id}>{result.run_id.slice(0, 12)}</span>
        <span className={`status-pill ${CURRENTNESS_PILL[currentness]}`} title={status.detail}><i aria-hidden="true" />{status.label}</span>
      </h3>
      <p className="caption">
        Scenario <span className="mono">{result.scenario_id}</span> rev {result.scenario_revision} · {EXECUTION_MODE_LABEL[result.provenance.execution_mode]} · search {result.provenance.search_version} seed {result.provenance.seed}
      </p>
      <div className={`c05-outcome tone-${outcome.tone}`} data-testid="search-outcome">
        <strong>{outcome.title}</strong>
        <span>{outcome.detail}</span>
      </div>
      {cards.length > 0 && nothingFeasible && (
        <p className="fine-print text-warning">This search finished with no feasible layout. Nothing below is recommended; the constraint records explain why.</p>
      )}
      {cards.length === 0 ? <p className="fine-print">The result contains no evaluated layouts.</p> : (
        <table className="layout-table c05-table">
          <caption className="sr-only">Layouts evaluated by this search</caption>
          <thead><tr><th scope="col">Layout</th><th scope="col">Shade</th><th scope="col">Cost · trees</th><th scope="col">Model feasibility</th></tr></thead>
          <tbody>
            {cards.map(card => {
              const shown = selectedLayoutId === card.layoutId
              return (
                <tr key={`${card.layoutId}@${card.revision}`} className={shown ? 'c05-row-shown' : undefined}>
                  <th scope="row">
                    <button type="button" className="text-action" aria-pressed={shown} onClick={() => onSelectLayout(shown ? null : card.layoutId)}>
                      {card.title}
                    </button>
                    <small title={`${card.layoutId}@${card.revision}`}>{card.layoutId.length > 18 ? `…${card.layoutId.slice(-14)}` : card.layoutId}@{card.revision}</small>
                    <small>{card.placements.map(p => `E ${p.position_enu_m[0]}, N ${p.position_enu_m[1]}`).join(' · ')}</small>
                  </th>
                  <td><ShadeCell card={card} /></td>
                  <td>{spendText(card, formatPence)}<small>{card.treeCount} tree{card.treeCount === 1 ? '' : 's'}{card.maxTreeCount !== null ? ` of max ${card.maxTreeCount}` : ''}</small></td>
                  <td>
                    <span className={`status-pill ${FEASIBILITY_PILL[card.feasibility]}`}><i aria-hidden="true" />{FEASIBILITY_LABEL[card.feasibility]}</span>
                    <small>{card.counts.fail ? `${card.counts.fail} fail · ` : ''}{card.counts.unknown ? `${card.counts.unknown} unknown · ` : ''}{card.counts.pass} pass</small>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
      {bestCaptionApplies(result.analytical_outcome, cards) && <p className="caption">{bestLayoutCaption(record.inputScenario?.input.objective.kind ?? null)}</p>}
      <details className="evidence-details">
        <summary>Constraint explanations ({result.constraints.length})</summary>
        <ul>
          {cards.flatMap(card => [
            ...card.reasons.map((reason, i) => <li key={`${card.layoutId}@${card.revision}-r-${i}`}>{card.layoutId}: {reason}</li>),
            ...card.constraints.map((c, i) => (
              <li key={`${card.layoutId}@${card.revision}-c-${i}`} className={c.status === 'pass' ? undefined : 'text-warning'}>
                {card.layoutId} · {c.rule}: <strong>{c.status}</strong>
                {c.observed_value !== null ? ` (observed ${c.observed_value}${c.unit ? ` ${c.unit}` : ''}${c.limit !== null ? `, limit ${c.limit}` : ''})` : ''}
                {c.evidence.length ? ` — ${c.evidence.join('; ')}` : ''}
              </li>
            )),
          ])}
        </ul>
      </details>
      {result.limitations.length > 0 && <p className="fine-print text-warning">{result.limitations.join(' ')}</p>}
      <h3 className="section-title c05-ranking">Candidate ranking</h3>
      <p className="fine-print">{RANKING_UNAVAILABLE}</p>
    </div>
  )
}

function MetricValue({ metric }: { metric: Metric }) {
  return <><strong className="mono">{formatValue(metric.value)}</strong> {unitLabel(metric.unit)}</>
}

/** Primary-case unweighted shade; another case only with its note; the weighted score kept apart. */
function ShadeCell({ card }: { card: LayoutCard }) {
  const metric = card.shade ?? card.otherCaseShade
  const note = shadeNote(card)
  const score = scoreNote(card, formatValue, unitLabel)
  return (
    <>
      {metric ? <MetricValue metric={metric} /> : <em>no shade metric</em>}
      {note && <small className={card.shade ? undefined : 'text-warning'}>{note}</small>}
      {score && <small>{score}</small>}
    </>
  )
}
