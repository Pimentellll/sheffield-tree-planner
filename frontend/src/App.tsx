import { useMemo, useState } from 'react'
import SiteScene from './scene/SiteScene'
import { checkSiteTransform } from './scene/transform'
import { useWorkspace } from './planning/useWorkspace'
import { EvaluationControls, ResultCard, RunHistory, SiteStatus, TreeEditor } from './panels/Panels'
import { ProposalReviewPanel, RequirementsPanel } from './panels/Requirements'
import { AlternativesPanel } from './panels/Alternatives'
import CompareScreen from './panels/CompareScreen'
import ReportScreen from './panels/ReportScreen'
import OverviewScreen from './panels/OverviewScreen'
import { layoutRows, objectiveView } from './planning/alternatives'
import type { Vec3 } from './api/types'
import { CURRENTNESS_LABEL, formatPence, formatValue, nearestCandidate, primaryMetric, samePosition, stepCandidate, unitLabel } from './planning/evaluation'
import { IconArrow, IconAlert, IconChat, IconCheck, IconCompare, IconDownload, IconMap, IconReport, IconSliders, IconTree } from './ui/icons'
import type { ReactNode } from 'react'

type Screen = 'overview' | 'studio' | 'compare' | 'report'
const screens: { id: Screen; number: string; label: string; icon: ReactNode }[] = [
  { icon: <IconMap />, id: 'overview', number: '01', label: 'Sheffield sites' },
  { icon: <IconSliders />, id: 'studio', number: '02', label: 'Planning studio' },
  { icon: <IconCompare />, id: 'compare', number: '03', label: 'Compare' },
  { icon: <IconReport />, id: 'report', number: '04', label: 'Review pack' },
]

function App() {
  const [screen, setScreen] = useState<Screen>('studio')
  const ws = useWorkspace()
  const transform = useMemo(() => (ws.site ? checkSiteTransform(ws.site) : null), [ws.site])
  const primaryCase = ws.scenario?.input.evaluation_cases.find(c => c.case_id === ws.scenario?.input.objective.primary_case_id) ?? null
  const treeState = ws.profile && primaryCase ? ws.profile.states[primaryCase.profile_state] ?? null : null
  const connected = ws.connection.status === 'connected'
  const synthetic = ws.site?.site_kind === 'synthetic_test'
  const scene = ws.declaration?.status === 'verified' ? ws.declaration.scene : null
  const catalogue = ws.site?.candidate_catalogue ?? []
  const candidateMode = catalogue.length > 0
  const candidates = useMemo(() => catalogue.map(c => ({ id: c.candidate_id, position: c.position_enu_m as Vec3, selected: Boolean(ws.draftPosition && samePosition(c.position_enu_m as Vec3, ws.draftPosition)) })), [catalogue, ws.draftPosition])
  // With a candidate catalogue the backend evaluates catalogue positions only, so moves snap to candidates.
  const moveTree = (p: Vec3) => {
    if (!candidateMode) { ws.setDraftPosition(p); return }
    const c = nearestCandidate(catalogue, p)
    if (c) ws.setDraftPosition(c.position_enu_m as Vec3)
  }
  const stepTree = (east: number, north: number) => {
    if (!ws.draftPosition) return
    const c = stepCandidate(catalogue, ws.draftPosition, east, north)
    if (c) ws.setDraftPosition(c.position_enu_m as Vec3)
  }
  const ops = ws.connection.status === 'connected' ? ws.connection.health.available_operations : []
  const [selectedLayoutId, setSelectedLayoutId] = useState<string | null>(null)
  const searchRecord = ws.runs.find(r => r.result?.operation === 'search_layouts') ?? null
  const overlays = useMemo(() => (searchRecord?.result ? layoutRows(searchRecord.result, searchRecord.inputScenario) : [])
    .filter(row => row.role !== 'baseline')
    .map(row => ({ id: row.layoutId, positions: row.placements.map(p => p.position_enu_m as Vec3), highlighted: row.layoutId === selectedLayoutId })), [searchRecord, selectedLayoutId])

  const evalRecord = ws.runs.find(r => r.job.operation === 'evaluate_layout' && r.result) ?? null
  const evalMetric = evalRecord?.result ? primaryMetric(evalRecord.result, ws.scenario?.input.objective.primary_case_id ?? null) : null
  const evalCurrentness = evalRecord?.result ? ws.currentness(evalRecord.result) : null
  const objective = ws.scenario ? objectiveView(ws.scenario) : null
  const constraints = ws.scenario?.input.constraints ?? null
  const dataPill = !connected ? 'OFFLINE · NO DATA' : synthetic ? 'SYNTHETIC TEST SITE · NOT SHEFFIELD' : 'SITE DATA · SEE PROVENANCE'
  const crumb = { overview: ['City overview', 'Sheffield sites'], studio: ['Optimisation Studio', ws.site?.name ?? 'No site loaded'], compare: ['Scenario comparison', ws.site?.name ?? 'No site loaded'], report: ['Reports', ws.site?.name ?? 'No site loaded'] }[screen]

  return (
    <div className={`app-shell screen-${screen}`}>
      <a className="skip-link" href="#main">Skip to content</a>
      <aside className="rail no-print">
        <div className="rail-logo" aria-label="CANOPY Sheffield"><IconTree /></div>
        <nav aria-label="Main navigation">
          {screens.map(item => <button key={item.id} type="button" title={item.label} className={`rail-item ${screen === item.id ? 'active' : ''}`} aria-current={screen === item.id ? 'page' : undefined} onClick={() => setScreen(item.id)}>{item.icon}<span className="sr-only">{item.label}</span></button>)}
        </nav>
        <div className="rail-foot" title={connected ? `Local workspace · API ${ws.connection.status === 'connected' ? ws.connection.health.version : ''}` : 'Local workspace · offline'}><span className={`status-dot${connected ? '' : ' warning'}`} /></div>
      </aside>

      <header className="topbar no-print">
        <div className="wordmark">CANOPY <span>Urban Intelligence · Sheffield</span></div>
        <div className="crumb"><span>{crumb[0]}</span><i aria-hidden="true">/</i><strong>{crumb[1]}</strong></div>
        <span className={`data-pill${connected && !synthetic ? ' ok' : ''}`} role="status" title={connected && synthetic ? `Every number is a live computation by the local backend on authored synthetic geometry. It is not a surveyed site or a forecast of real benefit. Available operations: ${ops.join(', ') || 'none'}.` : undefined}><i aria-hidden="true" />{dataPill}</span>
        <span className="topbar-status" data-testid="backend-status"><span className={`status-dot${connected ? '' : ' warning'}`} /> {connected ? 'Local backend connected' : ws.connection.status === 'connecting' ? 'Connecting…' : 'Backend not connected'}</span>
        <div className="topbar-actions">
          {screen !== 'studio' && <button type="button" className="ghost-btn" onClick={() => setScreen('studio')}><IconSliders /> Open studio</button>}
          {screen !== 'compare' && <button type="button" className="ghost-btn" onClick={() => setScreen('compare')}><IconCompare /> Compare plans</button>}
          {screen !== 'report' && <button type="button" className="ghost-btn" onClick={() => setScreen('report')}><IconDownload /> Report</button>}
        </div>
      </header>

      <main id="main" className="main-content">
          {screen === 'studio' ? <div className="studio">
            <aside className="param-panel" aria-label="Plan parameters">
              <div className="param-scroll">
                <div className="param-head">
                  <div className="param-title"><h1>Plan parameters</h1><span className="rev-tag">{ws.scenario ? `REV ${ws.scenario.revision}${ws.draftDirty ? ' · DRAFT' : ''}` : 'NO SCENARIO'}</span></div>
                  <p>{connected ? `${catalogue.length || 'No'} catalogue position${catalogue.length === 1 ? '' : 's'}${scene?.kind === 'physical' ? ` · ${scene.scene.samples.length} receiver samples` : ''}` : 'Start the local backend (see frontend/README.md). No numbers are shown without a backend run.'}</p>
                  {(synthetic || !connected) && <p className="param-note" data-testid="site-notice">{connected ? <><strong>Synthetic test site: not Sheffield.</strong> Every number is a live backend computation on authored geometry, not a surveyed site or a forecast of real benefit. Available: {ops.join(', ') || 'no operations'}.</> : <strong>Not connected to an evaluator.</strong>}</p>}
                </div>
                <RequirementsPanel ws={ws} />
                {objective && <section className="param-section">
                  <div className="param-section-head"><span>OBJECTIVE</span><em>1 modelled</em></div>
                  <div className="chip-row"><span className="chip active">Direct shade</span><span className="chip off" title="Not modelled by this backend">Flood</span><span className="chip off" title="Not modelled by this backend">Air quality</span><span className="chip off" title="Not modelled by this backend">Equity</span></div>
                  <div className="weight-row"><span><i className="sq heat" />Shade on targets</span><em>{ws.scenario?.input.objective.quantity_kind}</em><strong>100%</strong></div>
                  <div className="weight-track"><div style={{ width: '100%' }} /></div>
                  <p className="fine-print">{objective.text}{objective.target ? ` · target ${objective.target}` : ''}. Flood, air quality and equity are not computed here, so they cannot be weighted.</p>
                </section>}
                <TreeEditor ws={ws} profile={ws.profile} state={treeState} caseState={primaryCase?.profile_state ?? null} />
                {constraints && <section className="param-section">
                  <div className="param-section-head"><span>CONSTRAINTS</span><em>enforced by backend</em></div>
                  <ConstraintRow title={`Budget ${formatPence(constraints.budget_pence)}`} sub={`${constraints.budget_basis} · hard limit`} />
                  <ConstraintRow title={constraints.max_tree_count == null ? 'No tree-count limit' : `At most ${constraints.max_tree_count} trees`} sub="Tree count" on={constraints.max_tree_count != null} />
                  <ConstraintRow title={constraints.spacing_rules.length ? `Min. ${constraints.spacing_rules.map(r => r.minimum_centre_separation_m).join(' / ')} m between trees` : 'No spacing rule declared'} sub="Centre separation" on={constraints.spacing_rules.length > 0} />
                  <ConstraintRow title={constraints.winter_limits.length ? `Protect winter sun ≤ ${constraints.winter_limits.map(w => w.maximum_loss_m2_h).join(' / ')} m²·h` : 'No winter limit declared'} sub={constraints.winter_limits.map(w => w.case_id).join(', ') || 'Winter check'} on={constraints.winter_limits.length > 0} />
                  <ConstraintRow title="Respect exclusion zones" sub={`${ws.site?.exclusions.length ?? 0} region${(ws.site?.exclusions.length ?? 0) === 1 ? '' : 's'} in this SiteBundle`} on={(ws.site?.exclusions.length ?? 0) > 0} />
                  <ConstraintRow title="Survey still required" sub={constraints.survey_requirements.join('; ') || 'Utilities, soil, ownership, permits: unknown'} warn />
                </section>}
              </div>
              <div className="param-foot">
                <EvaluationControls ws={ws} />
              </div>
            </aside>

            <section className="site-panel map-stage" aria-labelledby="site-heading">
              <h2 id="site-heading" className="sr-only">{ws.site?.name ?? 'No site loaded'}</h2>
              <SiteScene scene={scene} candidates={candidates} onStep={candidateMode ? stepTree : undefined} treeState={treeState} committed={ws.committedPosition} draft={ws.draftPosition} editable={connected && Boolean(ws.draftPosition)} onDraftChange={moveTree} siteLabel={synthetic ? 'SYNTHETIC TEST SITE' : ws.site ? 'SITE' : 'NO SITE'} overlays={overlays} />
              <div className="map-chips" aria-hidden="true">
                <span className="map-chip"><i className="sq lime" />Proposed tree</span>
                {scene?.kind === 'physical' && <span className="map-chip"><i className="sq water" />Receiver samples</span>}
                {candidateMode && <span className="map-chip"><i className="ring" />Candidates</span>}
                {overlays.length > 0 && <span className="map-chip"><i className="sq sky" />Search options</span>}
              </div>
              {evalRecord?.result && evalMetric && <div className={`map-toast${evalCurrentness === 'current' ? '' : ' stale'}`} role="status">
                {evalCurrentness === 'current' ? <IconCheck /> : <IconAlert />}
                <span><strong>{evalCurrentness === 'current' ? 'Evaluation computed' : 'Last evaluation is not current'}</strong> · {formatValue(evalMetric.value)} {unitLabel(evalMetric.unit)} · rev {evalRecord.result.scenario_revision} · run {evalRecord.result.run_id.slice(0, 8)}</span>
                <button type="button" onClick={() => setScreen('compare')}>See evidence</button>
              </div>}
              <div className="map-legend"><strong>LEGEND</strong><span><i className="legend-dot proposed" /> Proposed tree</span>{ws.draftDirty && <span><i className="legend-dot ghost" /> Last evaluated position</span>}{scene?.kind === 'reference' && <><span><i className="legend-dot target" /> Target receiver (represented area)</span><span><i className="legend-line sun" /> Declared sun direction (input, view only)</span></>}{scene?.kind === 'physical' && <><span><i className="legend-dot target" /> Receiver samples ({scene.scene.samples.length})</span><span><i className="legend-line region" /> Planting region</span></>}{candidateMode && <span><i className="legend-dot candidate" /> Catalogue positions ({catalogue.length})</span>}{overlays.length > 0 && <span><i className="legend-dot option" /> Search option placements</span>}<span className="legend-hint">{candidateMode ? 'Drag tree to snap between catalogue positions' : 'Drag tree to move'} · drag elsewhere to orbit · scroll to zoom</span></div>
              <div className="map-foot">{synthetic ? 'Authored synthetic geometry · not survey-grade' : 'Geometry from the verified SiteBundle asset'}</div>
            </section>

            <aside className="detail-panel result-panel" aria-label="Planning controls and evidence">
              <div className="result-head">
                <div className="result-status"><span className={`status-dot${evalCurrentness === 'current' ? '' : ' warning'}`} />{evalCurrentness ? CURRENTNESS_LABEL[evalCurrentness].label.split(' ')[0] : 'NO RESULT'}{ws.scenario ? ` · REV ${ws.scenario.revision}` : ''}{evalRecord?.result ? ` · ${evalRecord.result.provenance.compute_finished_at_utc.slice(11, 16)} UTC` : ''}</div>
                <h2>{ws.site?.name ?? 'No site loaded'}</h2>
                {objective && <p>{objective.text}</p>}
              </div>
              <ResultCard ws={ws} />
              <AlternativesPanel ws={ws} selectedLayoutId={selectedLayoutId} onSelectLayout={setSelectedLayoutId} />
              <ProposalReviewPanel ws={ws} />
              <RunHistory ws={ws} />
              <SiteStatus ws={ws} transform={transform} />
              <div className="detail-section agent-box">
                <div className="agent-title"><IconChat /> Investigate with the planning agent</div>
                <div className="agent-input" aria-disabled="true"><span>No agent endpoint on this backend yet</span><i><IconArrow /></i></div>
                <p className="fine-print">When the local model is connected, its answers will re-run these planning tools and cite each run. Nothing is scripted in its place.</p>
              </div>
            </aside>
          </div> : <div className="page-content">
            {screen === 'compare' ? <CompareScreen ws={ws} scene={scene} candidates={candidates} treeState={treeState} /> : screen === 'report' ? <ReportScreen ws={ws} /> : <OverviewScreen ws={ws} onOpenStudio={() => setScreen('studio')} />}
          </div>}
      </main>
    </div>
  )
}

function ConstraintRow({ title, sub, on = true, warn = false }: { title: string; sub: string; on?: boolean; warn?: boolean }) {
  return <div className="constraint-row"><div><strong>{title}</strong><span>{sub}</span></div>{warn ? <span className="lock-tag warn">SURVEY</span> : <span className={`toggle${on ? ' on' : ''}`} role="img" aria-label={on ? 'Enforced by the backend (read-only)' : 'Not declared in this scenario'}><i /></span>}</div>
}

export default App
