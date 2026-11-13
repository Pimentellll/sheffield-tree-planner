import { useMemo, useState } from 'react'
import SiteScene from './scene/SiteScene'
import { checkSiteTransform } from './scene/transform'
import { useWorkspace } from './planning/useWorkspace'
import { EvaluationControls, ResultCard, RunHistory, SiteStatus, TreeEditor } from './panels/Panels'
import { ProposalReviewPanel, RequirementsPanel } from './panels/Requirements'
import { AlternativesPanel } from './panels/Alternatives'
import { layoutRows } from './planning/alternatives'
import type { Vec3 } from './api/types'

type Screen = 'overview' | 'studio' | 'compare' | 'report'
const screens: { id: Screen; number: string; label: string }[] = [
  { id: 'overview', number: '01', label: 'City overview' },
  { id: 'studio', number: '02', label: 'Planning studio' },
  { id: 'compare', number: '03', label: 'Compare' },
  { id: 'report', number: '04', label: 'Report' },
]

function App() {
  const [screen, setScreen] = useState<Screen>('studio')
  const selected = screens.find(item => item.id === screen)!
  const ws = useWorkspace()
  const transform = useMemo(() => (ws.site ? checkSiteTransform(ws.site) : null), [ws.site])
  const primaryCase = ws.scenario?.input.evaluation_cases.find(c => c.case_id === ws.scenario?.input.objective.primary_case_id) ?? null
  const treeState = ws.profile && primaryCase ? ws.profile.states[primaryCase.profile_state] ?? null : null
  const connected = ws.connection.status === 'connected'
  const synthetic = ws.site?.site_kind === 'synthetic_test'
  const declaration = ws.declaration?.status === 'verified' ? ws.declaration.declaration : null
  const [selectedLayoutId, setSelectedLayoutId] = useState<string | null>(null)
  const searchRecord = ws.runs.find(r => r.result?.operation === 'search_layouts') ?? null
  const overlays = useMemo(() => (searchRecord?.result ? layoutRows(searchRecord.result, searchRecord.inputScenario) : [])
    .filter(row => row.role !== 'baseline')
    .map(row => ({ id: row.layoutId, positions: row.placements.map(p => p.position_enu_m as Vec3), highlighted: row.layoutId === selectedLayoutId })), [searchRecord, selectedLayoutId])

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">Skip to content</a>
      <aside className="sidebar">
        <div className="brand" aria-label="CANOPY Sheffield"><span className="brand-mark" aria-hidden="true">✳</span><span>CANOPY<span className="brand-place">SHEFFIELD</span></span></div>
        <p className="nav-caption">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {screens.map(item => <button key={item.id} type="button" className={`nav-item ${screen === item.id ? 'active' : ''}`} aria-current={screen === item.id ? 'page' : undefined} onClick={() => setScreen(item.id)}><span className="nav-number">{item.number}</span>{item.label}<span className="nav-arrow" aria-hidden="true">↗</span></button>)}
        </nav>
        <div className="sidebar-foot"><span className={`status-dot${connected ? '' : ' warning'}`} /> Local workspace <span className="muted">· {connected ? `API ${ws.connection.status === 'connected' ? ws.connection.health.version : ''}` : 'offline'}</span></div>
      </aside>

      <main id="main" className="main-content">
        <header className="topbar"><div className="mobile-brand">CANOPY <span>SHEFFIELD</span></div><span className="topbar-label">EVIDENCE LED TREE PLANNING</span><span className="topbar-status" data-testid="backend-status"><span className={`status-dot${connected ? '' : ' warning'}`} /> {connected ? 'Local backend connected' : ws.connection.status === 'connecting' ? 'Connecting…' : 'Backend not connected'}</span></header>
        <div className="page-content">
          <div className="eyebrow">WORKSPACE / {selected.number} / {selected.label.toUpperCase()}</div>
          {screen === 'studio' ? <>
            <div className="page-heading"><div><h1>Planting studio<span className="heading-dot">.</span></h1><p>Place one tree, evaluate it on the local engine, and see exactly which run the number came from.</p></div><span className="pill pill-muted">M2 VERTICAL SLICE</span></div>
            {(synthetic || !connected) && <div className="notice" role="status"><span className="notice-icon" aria-hidden="true">ⓘ</span><div><strong>{connected ? 'Synthetic reference site' : 'Not connected to an evaluator'}</strong><p>{connected ? 'This site is an explicit synthetic test declaration, not Sheffield. Results are real computations of that synthetic geometry with a chosen sun direction; feasibility and constraints are not evaluated.' : 'Start the local backend (see frontend/README.md). No numbers are shown without a backend run.'}</p></div></div>}
            <div className="studio-grid">
              <section className="site-panel" aria-labelledby="site-heading"><div className="panel-head"><div><span className="section-kicker">ACTIVE SITE</span><h2 id="site-heading">{ws.site?.name ?? 'No site loaded'}</h2></div><span className="tiny-tag">{synthetic ? 'SYNTHETIC TEST' : ws.site ? ws.site.site_kind.toUpperCase() : 'OFFLINE'}</span></div>
                <SiteScene declaration={declaration} treeState={treeState} committed={ws.committedPosition} draft={ws.draftPosition} editable={connected && Boolean(ws.draftPosition)} onDraftChange={ws.setDraftPosition} siteLabel={synthetic ? 'SYNTHETIC TEST SITE' : ws.site ? 'SITE' : 'NO SITE'} overlays={overlays} />
                <div className="map-legend"><span><i className="legend-dot proposed" /> Proposed tree</span>{ws.draftDirty && <span><i className="legend-dot ghost" /> Last evaluated position</span>}<span><i className="legend-dot target" /> Target receiver (represented area)</span><span><i className="legend-line sun" /> Declared sun direction (input, view only)</span>{overlays.length > 0 && <span><i className="legend-dot option" /> Search option placements</span>}<span>Drag tree to move · drag elsewhere to orbit · scroll to zoom</span></div>
              </section>
              <aside className="detail-panel" aria-label="Planning controls and evidence">
                <ResultCard ws={ws} />
                <EvaluationControls ws={ws} />
                <TreeEditor ws={ws} profile={ws.profile} state={treeState} caseState={primaryCase?.profile_state ?? null} />
                <AlternativesPanel ws={ws} selectedLayoutId={selectedLayoutId} onSelectLayout={setSelectedLayoutId} />
                <RequirementsPanel ws={ws} />
                <ProposalReviewPanel ws={ws} />
                <RunHistory ws={ws} />
                <SiteStatus ws={ws} transform={transform} />
              </aside>
            </div>
          </> : <section className="future-screen"><span className="section-kicker">{selected.number} / {selected.label.toUpperCase()}</span><h1>{screen === 'overview' ? 'Sheffield city overview' : screen === 'compare' ? 'Scenario comparison' : 'Impact & investment report'}<span className="heading-dot">.</span></h1><p>{screen === 'overview' ? 'Citywide layers and an audited Sheffield site are awaiting source and rights checks.' : screen === 'compare' ? 'Comparable plans will appear when genuine evaluated alternatives are available.' : 'A source checked report will be available once validated results and export rights exist.'}</p><div className="future-card"><span className="future-glyph" aria-hidden="true">↗</span><strong>Evidence required</strong><span>No illustrative metrics are shown as planning outcomes.</span></div><button type="button" className="text-action" onClick={() => setScreen('studio')}>Return to planning studio →</button></section>}
        </div>
      </main>
    </div>
  )
}

export default App
