import { useState } from 'react'
import SyntheticScene from './scene/SyntheticScene'

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
        <header className="topbar"><div className="mobile-brand">CANOPY <span>SHEFFIELD</span></div><span className="topbar-label">EVIDENCE LED TREE PLANNING</span><span className="topbar-status"><span className="status-dot warning" /> Backend not connected</span></header>
        <div className="page-content">
          <div className="eyebrow">WORKSPACE / {selected.number} / {selected.label.toUpperCase()}</div>
          {screen === 'studio' ? <>
            <div className="page-heading"><div><h1>Planting studio<span className="heading-dot">.</span></h1><p>Explore the site geometry before connecting a measured planning run.</p></div><span className="pill pill-muted">FRONTEND FOUNDATION</span></div>
            <div className="notice" role="status"><span className="notice-icon" aria-hidden="true">ⓘ</span><div><strong>Synthetic scene preview</strong><p>This geometry is invented for interface development. No Sheffield site, planting position, shade benefit, cost or feasibility has been evaluated.</p></div></div>
            <div className="studio-grid">
              <section className="site-panel" aria-labelledby="site-heading"><div className="panel-head"><div><span className="section-kicker">ACTIVE SITE</span><h2 id="site-heading">Synthetic test garden</h2></div><span className="tiny-tag">TEST DATA</span></div><SyntheticScene /><div className="map-legend"><span><i className="legend-dot existing" /> Existing tree (illustrative)</span><span><i className="legend-dot target" /> Target region (illustrative)</span><span>Drag to orbit · Right drag to pan · Scroll to zoom</span></div></section>
              <aside className="detail-panel" aria-label="Site and calculation status"><div className="detail-section"><span className="section-kicker">SITE READINESS</span><h2>Explore the shape.<br />Check the evidence.</h2><p>The scene is a spatial UI fixture only. It cannot establish planting suitability or quantify shade.</p><div className="readiness-row"><span>Geometry source</span><strong>Synthetic fixture</strong></div><div className="readiness-row"><span>Analysis frame</span><strong>Provisional ENU</strong></div><div className="readiness-row"><span>Real site audit</span><strong className="text-warning">Pending</strong></div></div><div className="detail-section result-section"><span className="section-kicker">CURRENT RESULT</span><div className="empty-visual" aria-hidden="true"><span>—</span></div><h3>No calculation available</h3><p>The evaluation API and numerical engine have not been connected. Results will appear here with run identity, units and source status when available.</p><button type="button" disabled className="primary-action">Evaluate planting <span aria-hidden="true">↗</span></button><p className="disabled-caption">Available after the evaluator API is integrated.</p></div></aside>
            </div>
          </> : <section className="future-screen"><span className="section-kicker">{selected.number} / {selected.label.toUpperCase()}</span><h1>{screen === 'overview' ? 'Sheffield city overview' : screen === 'compare' ? 'Scenario comparison' : 'Impact & investment report'}<span className="heading-dot">.</span></h1><p>{screen === 'overview' ? 'Citywide layers and an audited Sheffield site are awaiting source and rights checks.' : screen === 'compare' ? 'Comparable plans will appear when genuine evaluated alternatives are available.' : 'A source checked report will be available once validated results and export rights exist.'}</p><div className="future-card"><span className="future-glyph" aria-hidden="true">↗</span><strong>Evidence required</strong><span>No illustrative metrics are shown as planning outcomes.</span></div><button type="button" className="text-action" onClick={() => setScreen('studio')}>Return to planning studio →</button></section>}
        </div>
      </main>
    </div>
  )
}

export default App
