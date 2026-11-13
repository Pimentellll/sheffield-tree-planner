import { useEffect, useState } from 'react'
import type { JobRequest, Scenario } from '../api/types'
import { describeValue, formatPence, parsePounds, poundsText } from '../planning/evaluation'
import type { Workspace } from '../planning/useWorkspace'
import { FOCUS_TARGET, focusAfterRender } from './focus'

/** Budget, tree-count and exclusion edits stay a draft until a human accepts them. */
export function RequirementsPanel({ ws }: { ws: Workspace }) {
  const draft = ws.draftRequirements
  const accepted = ws.acceptedRequirements
  const editable = ws.connection.status === 'connected' && Boolean(draft)
  // Initialised from the draft so the fields are never blank when the editor opens.
  const [budgetText, setBudgetText] = useState(() => (draft ? poundsText(draft.budgetPence) : ''))
  const [countText, setCountText] = useState(() => (draft && draft.maxTreeCount !== null ? String(draft.maxTreeCount) : ''))
  const [budgetError, setBudgetError] = useState<string | null>(null)
  const [countError, setCountError] = useState<string | null>(null)

  useEffect(() => { if (draft) { setBudgetText(poundsText(draft.budgetPence)); setBudgetError(null) } }, [draft?.budgetPence]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (draft) { setCountText(draft.maxTreeCount === null ? '' : String(draft.maxTreeCount)); setCountError(null) } }, [draft?.maxTreeCount]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!draft || !accepted || !ws.scenario) return null
  const constraints = ws.scenario.input.constraints
  const exclusions = ws.site?.exclusions ?? []

  const commitBudget = () => {
    const pence = parsePounds(budgetText)
    if (pence === null) { setBudgetError('Enter an amount in pounds, e.g. 100 or 99.50.'); return }
    setBudgetError(null)
    ws.setDraftRequirements({ ...draft, budgetPence: pence })
  }
  const commitCount = () => {
    const text = countText.trim()
    if (text === '') { setCountError(null); ws.setDraftRequirements({ ...draft, maxTreeCount: null }); return }
    if (!/^\d{1,5}$/.test(text)) { setCountError('Enter a whole number, or leave blank for no limit.'); return }
    setCountError(null)
    ws.setDraftRequirements({ ...draft, maxTreeCount: Number(text) })
  }
  const toggleExclusion = (id: string) => {
    const set = new Set(draft.excludedRegionIds)
    if (set.has(id)) set.delete(id); else set.add(id)
    ws.setDraftRequirements({ ...draft, excludedRegionIds: [...set].sort() })
  }

  return (
    <div className="detail-section">
      <span className="section-kicker">REQUIREMENTS</span>
      <h3 className="section-title">
        Accepted revision {ws.scenario.revision}
        {ws.draftDirty ? <span className="tag tag-warning" data-testid="draft-badge">DRAFT · NOT ACCEPTED</span> : <span className="tag tag-ok">NO DRAFT EDITS</span>}
      </h3>
      <div className="field-grid">
        <label className="number-field">
          <span>Budget £</span>
          <input aria-label="Upfront budget in pounds" inputMode="decimal" value={budgetText} disabled={!editable}
            onChange={e => setBudgetText(e.target.value)} onBlur={commitBudget} onKeyDown={e => { if (e.key === 'Enter') commitBudget() }} />
        </label>
        <label className="number-field">
          <span>Max trees</span>
          <input aria-label="Maximum tree count (blank for no limit)" inputMode="numeric" placeholder="no limit" value={countText} disabled={!editable}
            onChange={e => setCountText(e.target.value)} onBlur={commitCount} onKeyDown={e => { if (e.key === 'Enter') commitCount() }} />
        </label>
      </div>
      {(budgetError || countError) && <p className="fine-print text-warning" role="alert">{budgetError ?? countError}</p>}
      <p className="fine-print">Accepted: {formatPence(accepted.budgetPence)} {constraints.budget_basis} budget · {accepted.maxTreeCount === null ? 'no tree-count limit' : `at most ${accepted.maxTreeCount} trees`}.</p>
      <div className="exclusions">
        <span className="fine-label">Exclusion regions</span>
        {exclusions.length === 0
          ? <p className="fine-print">This SiteBundle defines no exclusion regions, so none can be selected.</p>
          : exclusions.map(e => (
            <label key={e.feature_id} className="check-row">
              <input type="checkbox" disabled={!editable} checked={draft.excludedRegionIds.includes(e.feature_id)} onChange={() => toggleExclusion(e.feature_id)} />
              <span>{e.feature_id}</span><em>{e.evidence_status}</em>
            </label>
          ))}
      </div>
      <details className="evidence-details">
        <summary>Other hard constraints (read-only here)</summary>
        <ul>
          <li>Allowed profiles: {constraints.allowed_profile_ids.join(', ') || 'none'}</li>
          <li>Spacing rules: {constraints.spacing_rules.length ? constraints.spacing_rules.map(r => `${r.minimum_centre_separation_m} m (${r.clearance_state})`).join('; ') : 'none declared'}</li>
          <li>Winter limits: {constraints.winter_limits.length ? constraints.winter_limits.map(w => `${w.case_id}: ≤ ${w.maximum_loss_m2_h} m²·h`).join('; ') : 'none declared'}</li>
          <li>Pinned placements: {constraints.pinned_placements.length}</li>
          <li>Survey requirements: {constraints.survey_requirements.length ? constraints.survey_requirements.join('; ') : 'none recorded'}</li>
        </ul>
      </details>
      {ws.draftDirty && (
        <div className="draft-box" data-testid="draft-changes" id={FOCUS_TARGET.draftChanges} tabIndex={-1}>
          <strong>Unaccepted changes</strong>
          {ws.draftChanges.length > 0
            ? <ul>{ws.draftChanges.map(c => <li key={c.path}><code>{c.path}</code>: {describeValue(c.before)} → {describeValue(c.after)}</li>)}</ul>
            : <p className="fine-print">Fix the highlighted fields to see the change set.</p>}
          {ws.requirementErrors.length > 0 && <p className="fine-print text-warning">{ws.requirementErrors.join(' ')}</p>}
          <p className="fine-print">Nothing is saved or computed yet. "Accept changes &amp; evaluate" saves these edits as a new accepted revision and then evaluates the current layout; earlier results become superseded.</p>
          <button type="button" className="text-action" onClick={() => { ws.revertDraft(); focusAfterRender(FOCUS_TARGET.editorToggle) }}>Discard draft</button>
        </div>
      )}
    </div>
  )
}

/** Server-side fixed-layout comparison of the accepted head and a hypothetical proposal; never accepts it. */
const compareScenariosRequest = (proposal: Scenario) => (head: Scenario, requestId: string): JobRequest => ({
  request_id: requestId,
  operation: 'compare_scenarios',
  scenario_ref: { scenario_id: head.scenario_id, revision: head.revision, scope: head.scope },
  arguments: {
    base_scenario_ref: { scenario_id: head.scenario_id, revision: head.revision, scope: head.scope },
    alternative_scenario_ref: { scenario_id: proposal.scenario_id, revision: proposal.revision, scope: proposal.scope },
    layout_refs: [head.input.proposed_layout_ref!],
    mode: 'fixed_layout',
  },
})

/** Human decision on a hypothetical scenario prepared elsewhere (e.g. by the planning agent). */
export function ProposalReviewPanel({ ws }: { ws: Workspace }) {
  const [id, setId] = useState('')
  const [revision, setRevision] = useState('1')
  if (ws.connection.status !== 'connected') return null
  const review = ws.review
  const compareAvailable = ws.connection.health.available_operations.includes('compare_scenarios')
  return (
    <div className="detail-section">
      <span className="section-kicker">PROPOSAL REVIEW</span>
      {!review ? (
        <>
          <p className="fine-print">Load a hypothetical scenario (for example one the planning agent prepared) to compare it with the accepted revision before deciding.</p>
          <form className="proposal-form" onSubmit={e => { e.preventDefault(); if (id.trim()) void ws.loadProposal(id.trim(), Number(revision) || 1) }}>
            <input aria-label="Proposal scenario id" placeholder="hypothetical scenario id" value={id} onChange={e => setId(e.target.value)} />
            <input aria-label="Proposal revision" inputMode="numeric" value={revision} onChange={e => setRevision(e.target.value)} />
            <button type="submit" className="secondary-action" disabled={!id.trim() || ws.busy !== null}>Load</button>
          </form>
        </>
      ) : (
        <div className="draft-box" data-testid="proposal-review">
          <strong>Proposal {review.proposal.scenario_id.slice(0, 8)}… rev {review.proposal.revision} <span className="tag tag-warning">HYPOTHETICAL</span></strong>
          <p className="fine-print">Based on accepted revision {review.proposal.base_scenario_ref?.revision ?? '—'}. Nothing in it has been computed or accepted.</p>
          {review.changes.length
            ? <ul>{review.changes.filter(c => c.path !== 'search.deadline_utc').map(c => <li key={c.path}><code>{c.path}</code>: {describeValue(c.before)} → {describeValue(c.after)}</li>)}</ul>
            : <p className="fine-print">No differences from the accepted revision.</p>}
          {!review.baseIsHead && <p className="fine-print text-warning">Its base is not the current accepted revision ({ws.scenario?.revision}), so the backend will refuse acceptance. Ask for a proposal based on the current revision.</p>}
          <div className="button-row">
            <button type="button" className="primary-action" disabled={!review.baseIsHead || ws.busy !== null || ws.draftDirty} onClick={() => void ws.acceptProposal()}>Accept proposal &amp; recompute</button>
            <button type="button" className="secondary-action" disabled={!compareAvailable || ws.busy !== null} onClick={() => void ws.submit(compareScenariosRequest(review.proposal))}>Compare with accepted on the backend</button>
            <button type="button" className="secondary-action" onClick={ws.dismissProposal}>Reject (dismiss)</button>
          </div>
          {ws.draftDirty && <p className="fine-print">Discard or accept your own draft first.</p>}
          <p className="fine-print">Rejecting only closes this review; the backend keeps the hypothetical as an unaccepted record.</p>
        </div>
      )}
    </div>
  )
}
