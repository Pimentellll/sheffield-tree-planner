import { useEffect, useMemo, useState } from 'react'
import SiteScene from './scene/SiteScene'
import { checkSiteTransform } from './scene/transform'
import { useWorkspace } from './planning/useWorkspace'
import { EvaluationControls, ResultCard, RunHistory, SiteStatus, TreeEditor } from './panels/Panels'
import { ProposalReviewPanel, RequirementsPanel } from './panels/Requirements'
import { AlternativesPanel } from './panels/Alternatives'
import CompareScreen from './panels/CompareScreen'
import ReportScreen from './panels/ReportScreen'
import OverviewScreen from './panels/OverviewScreen'
import { AgentPanel, ContextHeader, DraftBanner, EvidenceChainDetails, MapKey, NavigationRail, ProvenanceStrip, SCREENS, ScenarioStrip, type Screen } from './panels/Shell'
import { layoutRows } from './planning/alternatives'
import type { Vec3 } from './api/types'
import { nearestCandidate, samePosition, stepCandidate } from './planning/evaluation'

function App() {
  const [screen, setScreen] = useState<Screen>('studio')
  const selected = SCREENS.find(item => item.id === screen)!
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

  // The scenario editor (C01) opens by itself for a requirements draft; the user can close it.
  // A tree move alone does not open it, so the map key that explains the ghost tree stays visible.
  const [editorOpen, setEditorOpen] = useState(false)
  useEffect(() => { if (ws.requirementsDirty) setEditorOpen(true) }, [ws.requirementsDirty])

  return (
    <div className={`app-shell screen-${screen}`}>
      <a className="skip-link" href="#main">Skip to content</a>
      <NavigationRail screen={screen} onSelect={setScreen} connected={connected} />

      <main id="main" className={`main-content screen-${screen}`}>
        <ContextHeader ws={ws} screenTitle={selected.title} />
        {screen === 'studio' ? (
          <div className="studio">
            <h1 className="sr-only">Planting studio</h1>
            {/* DOM order is the reading and keyboard order: scenario first, then the scene, then results. */}
            <div className="studio-left">
              <ScenarioStrip ws={ws} editorOpen={editorOpen} onToggle={() => setEditorOpen(open => !open)} />
              <DraftBanner ws={ws} editorOpen={editorOpen} onReview={() => setEditorOpen(true)} />
              {(synthetic || !connected) && (
                <div className="notice glass-light" role="status" data-testid="site-notice">
                  <span className="notice-icon" aria-hidden="true">ⓘ</span>
                  <div><strong>{connected ? 'Synthetic test site: not Sheffield' : 'Not connected to an evaluator'}</strong><p>{connected
                    ? `Every metric is computed live by the local backend on this authored synthetic geometry and the assumptions listed with each result. It is not a surveyed site or a forecast of real benefit. Available here: ${ops.join(', ') || 'no operations'}. Each result states which constraints were evaluated and which remain unknown.`
                    : 'Start the local backend (see frontend/README.md). No metric is shown without a backend run.'}</p></div>
                </div>
              )}
              {editorOpen && (
                <aside id="scenario-editor" className="scenario-editor glass-light" aria-label="Scenario editor">
                  <RequirementsPanel ws={ws} />
                </aside>
              )}
            </div>

            <section className="site-panel studio-scene" aria-labelledby="site-heading">
              <h2 id="site-heading" className="sr-only">{ws.site?.name ?? 'No site loaded'}</h2>
              <SiteScene scene={scene} candidates={candidates} onStep={candidateMode ? stepTree : undefined} treeState={treeState} committed={ws.committedPosition} draft={ws.draftPosition} editable={connected && Boolean(ws.draftPosition)} onDraftChange={moveTree} siteLabel={synthetic ? 'SYNTHETIC TEST SITE' : ws.site ? 'SITE' : 'NO SITE'} overlays={overlays} framing={1.9} />
            </section>

            <div className="studio-right">
              <aside className="detail-panel" aria-label="Planning controls and evidence">
                <ResultCard ws={ws} />
                <EvaluationControls ws={ws} />
                <EvidenceChainDetails ws={ws} />
                <TreeEditor ws={ws} profile={ws.profile} state={treeState} caseState={primaryCase?.profile_state ?? null} />
                <AlternativesPanel ws={ws} selectedLayoutId={selectedLayoutId} onSelectLayout={setSelectedLayoutId} />
                {/* Human review of a prepared proposal stays reachable without opening the requirements editor. */}
                <ProposalReviewPanel ws={ws} />
                <RunHistory ws={ws} />
                <SiteStatus ws={ws} transform={transform} />
                <div className="detail-section card-actions">
                  <button type="button" className="secondary-action" onClick={() => setScreen('compare')}>Compare runs</button>
                  <button type="button" className="dark-action" onClick={() => setScreen('report')}>Open review pack</button>
                </div>
              </aside>
              <ProvenanceStrip ws={ws} />
            </div>

            {/* While the editor is open it takes the lower-left area (as in C01), so the key and agent bar give way. */}
            {!editorOpen && <MapKey scene={scene} dirty={ws.draftDirty} locationCount={new Set(catalogue.map(c => c.location_id)).size} optionCount={overlays.length} candidateMode={candidateMode} />}
            {!editorOpen && <AgentPanel ws={ws} />}
          </div>
        ) : (
          <div className="page-content">
            <div className="eyebrow">WORKSPACE / {selected.title.toUpperCase()}</div>
            {screen === 'compare' ? <CompareScreen ws={ws} scene={scene} candidates={candidates} treeState={treeState} /> : screen === 'report' ? <ReportScreen ws={ws} /> : <OverviewScreen ws={ws} />}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
