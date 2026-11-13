import type { Workspace } from '../planning/useWorkspace'

/**
 * Candidate sites from the STP-005 desk audit (docs/site-audit/STP-005-desk-audit.md, 12 Nov 2026).
 * Text and links only: no OSM, council or OS geometry is bundled, and neither candidate is an
 * accepted SiteBundle. Update this list only from that audit.
 */
const CANDIDATES = [
  {
    name: 'Weston Park',
    role: 'Primary geometry pilot candidate',
    facts: [
      'City park (Sheffield City Council)',
      'Grade II registered park and garden (Historic England 1001340): heritage review needed for any planting position',
      'EA 1 m composite DTM/DSM catalogue coverage; survey 16–17 March 2021',
    ],
    link: 'https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/weston-park',
  },
  {
    name: 'Manor Fields Park',
    role: 'Fallback geometry pilot',
    facts: ['District park (Sheffield City Council)', 'EA 1 m composite DTM/DSM catalogue coverage; survey 16–17 March 2021'],
    link: 'https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/parks-green-spaces',
  },
] as const

const OPEN_ITEMS = [
  'Download the intersecting EA DTM/DSM tiles and record tile IDs, SHA-256, vertical datum (ODN) and nodata',
  'Agree the shadow-casting context extent with Arnav (low-sun cutoff and obstruction heights)',
  'Verify a surveyed known point, true north, metre scale and the viewer transform',
  'Classify buildings, existing canopy and unknowns; never count a LiDAR crown twice',
  'Asset-level rights for local use, team sharing, public display and export',
]

export default function OverviewScreen({ ws }: { ws: Workspace }) {
  const active = ws.site
  return (
    <>
      <div className="page-heading"><div><h1>Sheffield sites<span className="heading-dot">.</span></h1><p>Where the planner can be used today, and what real Sheffield sites still need before any result there could be trusted.</p></div><span className="pill pill-muted">STP-005 STATUS</span></div>
      <div className="overview-grid">
        <section className="detail-panel" aria-labelledby="active-site">
          <div className="detail-section">
            <span className="section-kicker">LOADED IN THE PLANNER</span>
            <h2 id="active-site" className="card-title">{active ? active.name : 'No site loaded'}</h2>
            {active ? (
              <>
                <div className="readiness-row"><span>Kind</span><strong className={active.site_kind === 'synthetic_test' ? 'text-warning' : undefined}>{active.site_kind === 'synthetic_test' ? 'Synthetic test (not Sheffield)' : 'Real site'}</strong></div>
                <div className="readiness-row"><span>Scene / semantics</span><strong>rev {active.scene_revision} / {active.semantic_revision}</strong></div>
                <div className="readiness-row"><span>Blockers</span><strong>{active.readiness.blockers.length || 'none recorded'}</strong></div>
                <p className="fine-print">Only this site can be evaluated now. No real Sheffield geometry is in the application yet.</p>
              </>
            ) : <p className="fine-print">Start the local backend to load a site.</p>}
          </div>
        </section>
        {CANDIDATES.map(c => (
          <section key={c.name} className="detail-panel" aria-labelledby={`cand-${c.name}`}>
            <div className="detail-section">
              <span className="section-kicker">{c.role.toUpperCase()}</span>
              <h2 id={`cand-${c.name}`} className="card-title">{c.name}</h2>
              <span className="tag tag-warning">NOT ACCEPTED · V03 PENDING</span>
              <ul className="bin-list">{c.facts.map(f => <li key={f}>{f}</li>)}</ul>
              <a className="text-action" href={c.link} target="_blank" rel="noreferrer">Council page ↗</a>
            </div>
          </section>
        ))}
      </div>
      <section className="detail-panel overview-open" aria-labelledby="open-items">
        <div className="detail-section">
          <span className="section-kicker">BEFORE A REAL SITE CAN BE LOADED</span>
          <h2 id="open-items" className="card-title">Open items (desk audit, 12 Nov 2026)</h2>
          <ol className="bin-list">{OPEN_ITEMS.map(i => <li key={i}>{i}</li>)}</ol>
          <p className="fine-print">A public park name or downloadable data is not planting permission, a current tree inventory or a feasible position. See docs/site-audit/ for sources and licences.</p>
        </div>
      </section>
    </>
  )
}
