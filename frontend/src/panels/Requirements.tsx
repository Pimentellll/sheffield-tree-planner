import { useEffect, useState } from 'react'
import type { JobRequest, Scenario } from '../api/types'
import { describeValue, formatPence, parsePounds, poundsText } from '../planning/evaluation'
import { objectiveView } from '../planning/alternatives'
import type { Workspace } from '../planning/useWorkspace'
import { FOCUS_TARGET, focusAfterRender } from './focus'

/** Budget, tree-count and exclusion edits stay a draft until a human accepts them. */
export function RequirementsPanel({ ws, onClose }: { ws: Workspace; onClose?: () => void }) {
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

  // Typed text that is invalid or not yet applied to the draft blocks acceptance everywhere (via the workspace),
  // so a click can never accept an older draft than the value on screen.
  const livePence = parsePounds(budgetText)
  const countTrim = countText.trim()
  const budgetPending = draft ? livePence !== draft.budgetPence : false
  const countPending = draft ? (countTrim === '' ? draft.maxTreeCount !== null : !/^\d{1,5}$/.test(countTrim) || Number(countTrim) !== draft.maxTreeCount) : false
  const pending = Boolean(budgetError || countError || budgetPending || countPending)
  useEffect(() => { ws.setEditPending(pending) }, [pending]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => ws.setEditPending(false), []) // eslint-disable-line react-hooks/exhaustive-deps

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

  const n = ws.draftChanges.length
  const budgetChanged = draft.budgetPence !== accepted.budgetPence
  const countChanged = draft.maxTreeCount !== accepted.maxTreeCount
  const exclusionsChanged = [...draft.excludedRegionIds].sort().join('|') !== [...accepted.excludedRegionIds].sort().join('|')
  const primary = ws.scenario.input.evaluation_cases.find(c => c.case_id === ws.scenario!.input.objective.primary_case_id) ?? null
  const nextRevision = ws.scenario.revision + 1
  const Lock = () => <svg className="lock" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
  const locked = (label: string, value: string, note?: string) => (
    <div className="ed-locked" key={label}><div className="ed-row"><Lock /><span>{label}</span><b className="mono">{value}</b></div>{note && <p className="caption">{note}</p>}</div>
  )

  // C01 scenario editor. Editable: budget, tree-count limit, exclusions (what the backend lets a human change here).
  // Locked rows are the accepted scenario's own fields, shown read-only.
  return (
    <section className="ed" aria-labelledby="ed-title">
      <div className="ed-title-row">
        <h2 id="ed-title">Scenario</h2>
        {ws.draftDirty
          ? <span className="status-pill sp-warn" data-testid="draft-badge"><i aria-hidden="true" />{n > 0 ? `DRAFT · ${n} CHANGE${n === 1 ? '' : 'S'}` : 'DRAFT · NOT ACCEPTED'}</span>
          : <span className="status-pill sp-ok"><i aria-hidden="true" />NO DRAFT EDITS</span>}
        {onClose && <button type="button" id={FOCUS_TARGET.editorToggle} className="ed-close" aria-label="Close scenario editor" onClick={onClose}>×</button>}
      </div>
      <p className="caption mono ed-base">base: {ws.scenario.scenario_id.slice(0, 10)} rev {ws.scenario.revision} (accepted){ws.draftDirty ? ' · the draft has no analysis yet' : ''}</p>
      {ws.positionDirty && <p className="caption" data-testid="ghost-note">The proposed tree has moved: the faded tree in the view marks the last evaluated position.</p>}

      <div className={`ed-field${budgetChanged ? ' ed-changed' : ''}`}>
        <label className="ed-row" htmlFor="ed-budget"><span>Upfront budget (GBP)</span>{budgetChanged && <s className="mono">{formatPence(accepted.budgetPence)}</s>}</label>
        <div className="ed-input-row">
          <input id="ed-budget" aria-label="Upfront budget in pounds" inputMode="decimal" value={budgetText} disabled={!editable}
            onChange={e => setBudgetText(e.target.value)} onBlur={commitBudget} onKeyDown={e => { if (e.key === 'Enter') commitBudget() }} />
          {/* Echoes the TYPED text live (never the last applied value), so no stale figure sits beside a new one. */}
          <span className={`caption mono${livePence === null ? ' text-warning' : ''}`} data-testid="pence-echo">{livePence === null ? 'not a valid amount' : `= ${livePence.toLocaleString('en-GB')} pence`}</span>
        </div>
        <p className="caption">Basis: {constraints.budget_basis} only. Lifecycle cost is not a supported basis.</p>
      </div>
      <div className={`ed-field${countChanged ? ' ed-changed' : ''}`}>
        <label className="ed-row" htmlFor="ed-count"><span>Maximum trees</span>{countChanged && <s className="mono">{accepted.maxTreeCount === null ? 'no limit' : accepted.maxTreeCount}</s>}</label>
        <input id="ed-count" aria-label="Maximum trees (blank for no limit)" inputMode="numeric" placeholder="no limit" value={countText} disabled={!editable}
          onChange={e => setCountText(e.target.value)} onBlur={commitCount} onKeyDown={e => { if (e.key === 'Enter') commitCount() }} />
      </div>
      {(budgetError || countError) && <p className="fine-print text-warning" role="alert">{budgetError ?? countError}</p>}
      {pending && !budgetError && !countError && <p className="fine-print" data-testid="edit-pending">Press Enter to apply the typed value; nothing can be accepted until it is applied.</p>}
      <div className={`ed-field${exclusionsChanged ? ' ed-changed' : ''}`}>
        <span className="ed-row"><span>Exclusion regions</span>{exclusionsChanged && <s className="mono">{accepted.excludedRegionIds.join(', ') || 'none'}</s>}</span>
        {exclusions.length === 0
          ? <p className="caption">This SiteBundle defines no exclusion regions, so none can be selected.</p>
          : exclusions.map(e => (
            <label key={e.feature_id} className="check-row">
              <input type="checkbox" disabled={!editable} checked={draft.excludedRegionIds.includes(e.feature_id)} onChange={() => toggleExclusion(e.feature_id)} />
              <span>{e.feature_id}</span><em>{e.evidence_status}</em>
            </label>
          ))}
      </div>

      {locked('Objective', objectiveView(ws.scenario).text, 'Changed through a prepared proposal, not here.')}
      {primary && locked('Primary case', `${primary.case_id} · ${primary.role}`)}
      {locked('Tree spacing', constraints.spacing_rules.length ? constraints.spacing_rules.map(r => `≥ ${r.minimum_centre_separation_m} m (${r.clearance_state})`).join('; ') : 'none declared')}
      {locked('Winter limits', constraints.winter_limits.length ? constraints.winter_limits.map(w => `≤ ${w.maximum_loss_m2_h} m²·h · ${w.case_id}`).join('; ') : 'none declared')}
      {locked('Pinned trees', constraints.pinned_placements.length ? String(constraints.pinned_placements.length) : 'none')}
      {locked('Allowed profiles', constraints.allowed_profile_ids.join(', ') || 'none')}
      {locked('Survey requirements', constraints.survey_requirements.length ? constraints.survey_requirements.join('; ') : 'none recorded')}
      <div className="ed-future">
        <div className="ed-row"><Lock /><span>Heat, flood, air-quality, carbon weighting</span><span className="ed-future-tag mono">NOT COMPUTED</span></div>
        <p className="caption">No validated model exists, so this cannot be weighted. Shown so the boundary is visible, not as a control.</p>
      </div>

      {ws.draftDirty && (
        <>
          <div className="ed-summary" data-testid="draft-changes" id={FOCUS_TARGET.draftChanges} tabIndex={-1}>
            <span className="ed-summary-kicker mono">CHANGE SUMMARY</span>
            {n > 0
              ? <ul>{ws.draftChanges.map(c => <li key={c.path}><code>{c.path}</code>: {describeValue(c.before)} → {describeValue(c.after)}</li>)}</ul>
              : <p>Fix the highlighted fields to see the change set.</p>}
            {ws.requirementErrors.length > 0 && <p className="ed-summary-error">{ws.requirementErrors.join(' ')}</p>}
            <p className="ed-summary-note">Nothing is saved or computed yet. Accepting saves these edits as a new accepted revision and then evaluates the current layout; earlier results become superseded.</p>
          </div>
          <div className="ed-actions">
            <button type="button" className="secondary-action" onClick={() => { ws.revertDraft(); focusAfterRender(FOCUS_TARGET.editorToggle) }}>Discard draft</button>
            <button type="button" className="primary-action" disabled={!ws.canEvaluate} onClick={() => void ws.evaluate()}>Accept as rev {nextRevision} &amp; evaluate</button>
          </div>
        </>
      )}
    </section>
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
