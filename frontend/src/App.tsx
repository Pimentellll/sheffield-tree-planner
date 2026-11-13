import { useState } from 'react'
import SyntheticScene from './scene/SyntheticScene'
import { useReference } from './api/useReference'

type Screen = 'overview' | 'studio' | 'compare' | 'report'
const screens: { id: Screen; number: string; label: string }[] = [
  { id: 'overview', number: '01', label: 'City overview' },
  { id: 'studio', number: '02', label: 'Planning studio' },
  { id: 'compare', number: '03', label: 'Compare' },
  { id: 'report', number: '04', label: 'Report' },
]

function App() {
  const [screen, setScreen] = useState<Screen>('studio')
  const reference = useReference()
  const { session, status, error, busy, editing, display } = reference
  const selected = screens.find(item => item.id === screen)!

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">Skip to content</a>
      <aside className="sidebar">
        <div className="brand" aria-label="CANOPY Sheffield"><span className="brand-mark" aria-hidden="true">✳</span><span>CANOPY<span className="brand-place">SHEFFIELD</span></span></div>
        <p className="nav-caption">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {screens.map(item => <button key={item.id} type="button" className={`nav-item ${screen === item.id ? 'active' : ''}`} aria-current={screen === item.id ? 'page' : undefined} onClick={() => setScreen(item.id)}><span className="nav-number">{item.number}</span>{item.label}<span className="nav-arrow" aria-hidden="true">↗</span></button>)}
        </nav>
        <div className="sidebar-foot"><span className="status-dot" /> Local workspace <span className="muted">· Frontend preview</span></div>
      </aside>

      <main id="main" className="main-content">
        <header className="topbar"><div className="mobile-brand">CANOPY <span>SHEFFIELD</span></div><span className="topbar-label">EVIDENCE LED TREE PLANNING</span><span className="topbar-status"><span className={`status-dot ${session ? '' : 'warning'}`} /> {session ? 'Reference API connected' : 'Backend not connected'}</span></header>
        <div className="page-content">
          <div className="eyebrow">WORKSPACE / {selected.number} / {selected.label.toUpperCase()}</div>
          {screen === 'studio' ? <>
            <div className="page-heading"><div><h1>Planting studio<span className="heading-dot">.</span></h1><p>{session ? 'Explore and evaluate the synthetic reference.' : 'Explore the site geometry before connecting a measured planning run.'}</p></div><span className="pill pill-muted">{session ? 'REFERENCE API' : 'FRONTEND FOUNDATION'}</span></div>
            <div className="notice" role="status"><span className="notice-icon" aria-hidden="true">ⓘ</span><div><strong>{session ? 'Synthetic one-tree reference' : 'Synthetic scene preview'}</strong><p>{session ? 'Analytic chosen sun and toy opaque crown and trunk. This is not Sheffield, scientific acceptance, or planting feasibility approval.' : 'This geometry is invented for interface development. No Sheffield site, planting position, shade benefit, cost or feasibility has been evaluated.'}</p></div></div>
            <div className="studio-grid">
              <section className="site-panel" aria-labelledby="site-heading"><div className="panel-head"><div><span className="section-kicker">ACTIVE SITE</span><h2 id="site-heading">{session ? 'Synthetic one-tree reference' : 'Synthetic test garden'}</h2></div><span className="tiny-tag">TEST DATA</span></div><SyntheticScene session={session} /><div className="map-legend">{session ? <><span><i className="legend-dot existing" /> Proposed toy tree</span><span><i className="legend-dot target" /> Weighted receiver point · {session.scene.receiver_area_m2} m² represented</span><span>Grid is illustrative scale context · arrow: chosen sun</span></> : <><span><i className="legend-dot existing" /> Existing tree (illustrative)</span><span><i className="legend-dot target" /> Target region (illustrative)</span></>}<span>Drag to orbit · Right drag to pan · Scroll to zoom</span></div>{session && <p className="scene-binding" data-testid="scene-binding">ENU position {JSON.stringify(session.layout.placements[0]?.position_enu_m)} · analysis to viewer {JSON.stringify(session.site.analysis_to_viewer)} · scenario {session.scenario.scenario_id} revision {session.scenario.revision} · layout {session.layout.layout_id} revision {session.layout.revision}</p>}</section>
              <aside className="detail-panel" aria-label="Site and calculation status"><div className="detail-section"><span className="section-kicker">SITE READINESS</span><h2>Explore the shape.<br />Check the evidence.</h2><p>{session ? 'Synthetic inputs only. The receiver is a weighted point sample, not a surveyed area. Feasibility is not evaluated.' : 'The scene is a spatial UI fixture only. It cannot establish planting suitability or quantify shade.'}</p><div className="readiness-row"><span>Geometry source</span><strong>{session ? 'Synthetic reference' : 'Synthetic fixture'}</strong></div><div className="readiness-row"><span>Analysis frame</span><strong>{session ? 'ENU metres · site transform' : 'Provisional ENU'}</strong></div><div className="readiness-row"><span>Real site audit</span><strong className="text-warning">Pending</strong></div>{session && <div className="placement-controls"><p>Synthetic INPUT alternatives</p><button type="button" disabled={editing} onClick={() => void reference.place([0, -1, 0])}>Reference placement</button><button type="button" disabled={editing} onClick={() => void reference.place([3, -1, 0])}>Missed-tree placement</button></div>}</div><div className="detail-section result-section"><span className="section-kicker">CURRENT RESULT</span><p data-testid="calculation-state">{status}</p>{error && <p className="error-message" role="alert">{error}</p>}{display ? <><h3 data-testid="current-metric">{display.value} m²·h</h3><p>Additional geometric shade</p><div className="result-meta"><p data-testid="run-id">Run: {display.result.run_id}</p><p data-testid="scenario-revision">Scenario revision: {display.job.scenario_revision}</p><p data-testid="input-fingerprint">Input fingerprint: {display.job.input_fingerprint}</p><p>Source: reference integrity checked · {display.job.delivery?.execution_mode}</p></div></> : <><div className="empty-visual" aria-hidden="true"><span>—</span></div><h3>No current calculation</h3><p>Run the reference evaluator to show a current result with its identity and source status.</p></>}<button type="button" disabled={!session || busy || editing} className="primary-action" onClick={() => void reference.evaluate()}>Evaluate planting <span aria-hidden="true">↗</span></button>{!session && <p className="disabled-caption">Available when the reference API is connected.</p>}</div></aside>
            </div>
          </> : <section className="future-screen"><span className="section-kicker">{selected.number} / {selected.label.toUpperCase()}</span><h1>{screen === 'overview' ? 'Sheffield city overview' : screen === 'compare' ? 'Scenario comparison' : 'Impact & investment report'}<span className="heading-dot">.</span></h1><p>{screen === 'overview' ? 'Citywide layers and an audited Sheffield site are awaiting source and rights checks.' : screen === 'compare' ? 'Comparable plans will appear when genuine evaluated alternatives are available.' : 'A source checked report will be available once validated results and export rights exist.'}</p><div className="future-card"><span className="future-glyph" aria-hidden="true">↗</span><strong>Evidence required</strong><span>No illustrative metrics are shown as planning outcomes.</span></div><button type="button" className="text-action" onClick={() => setScreen('studio')}>Return to planning studio →</button></section>}
        </div>
      </main>
    </div>
  )
}

export default App
