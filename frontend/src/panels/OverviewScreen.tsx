import type { Workspace } from '../planning/useWorkspace'
import TerrainView from '../scene/TerrainView'

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

export default function OverviewScreen({ ws, onOpenStudio }: { ws: Workspace; onOpenStudio: () => void }) {
  const active = ws.site
  const synthetic = active?.site_kind === 'synthetic_test'
  return (
    <div className="overview">
      <div className="overview-main">
        <div className="hero">
          <span className="hero-kicker">SHEFFIELD · SITE READINESS</span>
          <h1>Plan greener streets. Prove the impact.</h1>
          <p>Where the planner can be used today, and what real Sheffield sites still need before any result there could be trusted. Site-level geometry, shade modelling and constraint checks run only inside a loaded study site.</p>
        </div>
        <div className="stat-row">
          <div className="stat"><span>Loaded in the planner</span><strong>{active ? 1 : 0}</strong><em>{active ? (synthetic ? 'synthetic test site' : 'site') : 'backend offline'}</em></div>
          <div className="stat"><span>Sheffield candidates</span><strong>{CANDIDATES.length}</strong><em>not accepted · V03 pending</em></div>
          <div className="stat warn"><span>Open audit items</span><strong>{OPEN_ITEMS.length}</strong><em>desk audit, 12 Nov 2026</em></div>
          <div className="stat"><span>Catalogue positions</span><strong>{active?.candidate_catalogue?.length ?? 0}</strong><em>in the loaded site</em></div>
        </div>
        <TerrainView name="weston-park" />
      </div>
      <aside className="ivory-card overview-side" aria-label="Sites and readiness">
        <div className="side-head"><h2>Study sites</h2><span>{CANDIDATES.length + (active ? 1 : 0)} listed</span></div>
        <p className="fine-print">A public park name or downloadable data is not planting permission, a current tree inventory or a feasible position.</p>
        <section className="site-row active" aria-labelledby="active-site">
          <i>1</i>
          <div>
            <h3 id="active-site">{active ? active.name : 'No site loaded'}</h3>
            {active ? <>
              <span className={`tag ${synthetic ? 'tag-warning' : 'tag-ok'}`}>{synthetic ? 'SYNTHETIC TEST · NOT SHEFFIELD' : 'REAL SITE'}</span>
              <p>scene rev {active.scene_revision} / semantics {active.semantic_revision} · blockers {active.readiness.blockers.length || 'none recorded'}</p>
              <p className="fine-print">Only this site can be evaluated now. Real terrain on this page is a view-only context; it is not loaded into the planner.</p>
            </> : <p className="fine-print">Start the local backend to load a site.</p>}
          </div>
        </section>
        {CANDIDATES.map((c, i) => (
          <section key={c.name} className="site-row" aria-labelledby={`cand-${c.name}`}>
            <i>{i + 2}</i>
            <div>
              <h3 id={`cand-${c.name}`}>{c.name}</h3>
              <span className="tag tag-warning">NOT ACCEPTED · V03 PENDING</span>
              <p>{c.role}</p>
              <ul className="bin-list">{c.facts.map(f => <li key={f}>{f}</li>)}</ul>
              <a className="text-action" href={c.link} target="_blank" rel="noreferrer">Council page ↗</a>
            </div>
          </section>
        ))}
        <details className="evidence-details" open>
          <summary id="open-items">Before a real site can be loaded ({OPEN_ITEMS.length})</summary>
          <ol>{OPEN_ITEMS.map(i => <li key={i}>{i}</li>)}</ol>
          <p className="fine-print">See docs/site-audit/ for sources and licences.</p>
        </details>
        <div className="next-step">
          <span>NEXT STEP</span>
          <strong>Optimise {active ? active.name : 'the loaded site'}</strong>
          <p>Shade modelling and constraint checks run only inside a study site.</p>
          <button type="button" className="primary-action" onClick={onOpenStudio}>Open Optimisation Studio <span aria-hidden="true">→</span></button>
        </div>
      </aside>
    </div>
  )
}
