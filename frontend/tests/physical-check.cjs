// Integrated UI check against Ben's synthetic physical runtime (scripts/serve_physical.py --winter)
// and the Vite dev server. Values are never hard-coded: each number on screen is compared with the
// backend's own stored record for the same run.
const { chromium } = require('playwright-core')
const { createHash } = require('node:crypto')
const { mkdirSync, readFileSync, writeFileSync, existsSync } = require('node:fs')
const { join } = require('node:path')

const browserPath = process.env.CANOPY_BROWSER || (process.platform === 'win32'
  ? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
  : ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(existsSync))
const url = process.env.CANOPY_URL || 'http://127.0.0.1:5173/'
const api = (process.env.CANOPY_API || 'http://127.0.0.1:8765').replace(/\/$/, '')
const evidenceDir = join(__dirname, '..', 'artifacts', 'physical')
mkdirSync(evidenceDir, { recursive: true })
const log = []
const check = (name, ok, detail = '') => { log.push({ name, ok: Boolean(ok), detail }); if (!ok) process.exitCode = 1; console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`) }
const hash = b => createHash('sha256').update(b).digest('hex')
const fmt = v => String(Number(v.toFixed(6)))

async function backend(method, path, body, headers = {}) {
  const r = await fetch(api + '/api/v1' + path, { method, headers: { Origin: new URL(api).origin, ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers }, body: body ? JSON.stringify(body) : undefined })
  const json = await r.json()
  if (!r.ok) throw new Error(`${method} ${path} -> ${r.status} ${JSON.stringify(json)}`)
  return json
}
async function head() {
  const s = await (await fetch(new URL('/canopy-dev-session.json', url))).json()
  let rev = s.scenario_ref.revision
  while ((await fetch(`${api}/api/v1/scenarios/${s.scenario_ref.scenario_id}?revision=${rev + 1}`)).status === 200) rev += 1
  return backend('GET', `/scenarios/${s.scenario_ref.scenario_id}?revision=${rev}`)
}
async function latest(op) {
  const h = await head()
  const sel = await backend('GET', `/scenarios/${h.scenario_id}/selections?revision=${h.revision}&scope=accepted`)
  const slot = op === 'search_layouts' ? 'search' : op === 'evaluate_layout' ? 'evaluation' : 'comparison'
  const job = sel[slot].current_job
  return job?.run_id ? backend('GET', `/results/${job.run_id}`) : null
}
async function waitJob(page, clickable) {
  const before = await page.evaluate(() => document.querySelector('.job-status span')?.textContent ?? '')
  await clickable.click()
  await page.waitForFunction(prev => {
    const job = document.querySelector('.job-status span')?.textContent ?? ''
    return (job !== prev && /Completed|Failed|Cancelled/.test(document.querySelector('.job-status strong')?.textContent ?? '')) || document.querySelector('.error-box[role=alert]')
  }, before, { timeout: 60000 })
  await page.waitForTimeout(500)
}
const shot = (page, name) => page.screenshot({ path: join(evidenceDir, `${name}.png`), fullPage: true })

;(async () => {
  const browser = await chromium.launch({ executablePath: browserPath, headless: true, args: ['--no-sandbox', '--no-proxy-server'] })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  const errors = []
  page.on('pageerror', e => errors.push(e.message))
  const nav = page.getByRole('navigation', { name: 'Main navigation' })
  try {
    const health = await backend('GET', '/health')
    check('physical runtime advertises evaluate, search and both comparisons', ['evaluate_layout', 'search_layouts', 'compare_locations', 'compare_scenarios'].every(o => health.available_operations.includes(o)), health.available_operations.join(','))
    await page.goto(url)
    await page.getByText('Local backend connected').waitFor({ timeout: 20000 })
    await page.waitForTimeout(800)
    const status = await page.locator('.detail-panel').last().innerText()
    check('physical scene bytes match the SiteBundle hash', /Hash matches · sha256/.test(status))
    const notice = await page.getByTestId('site-notice').innerText()
    check('banner is capability-based and no longer claims a chosen sun / unevaluated constraints', /not Sheffield/.test(notice) && /search_layouts/.test(notice) && !/chosen sun/.test(notice) && !/not evaluated/.test(notice))
    check('catalogue positions offered instead of free coordinates', await page.getByRole('radio', { name: /candidate-1/ }).count() === 1 && await page.getByRole('spinbutton').count() === 0)
    await shot(page, '01-loaded')

    // Evaluate the seeded layout.
    await waitJob(page, page.getByRole('button', { name: /Evaluate planting/ }))
    let r = await latest('evaluate_layout')
    const primary = (await head()).input.objective.primary_case_id
    let m = r.metrics.find(x => x.metric_id === 'additional_shade' && x.case_id === primary)
    check('evaluation metric equals the stored backend Result', (await page.getByTestId('metric-value').innerText()) === fmt(m.value), `${m.value} ${m.unit} (${r.provenance.execution_mode})`)
    check('evaluation is CURRENT and feasibility comes from the backend', /CURRENT\b/.test(await page.locator('.currentness strong').first().innerText()) && (await page.locator('.result-section').innerText()).includes(r.layouts[0].feasibility))

    // Search.
    await waitJob(page, page.getByRole('button', { name: 'Find planting options' }))
    const s = await latest('search_layouts')
    // "Completed" appears before the workspace has fetched the Result and its scenario snapshot; wait for the
    // stored layouts to be rendered (slow software WebGL in CI can take longer than waitJob's 500 ms).
    await page.waitForFunction(n => document.querySelectorAll('.layout-table tbody tr').length === n, s?.layouts.length ?? 0, { timeout: 15000 }).catch(() => {})
    const panel = await page.getByTestId('alternatives').innerText()
    check('search outcome shown for the stored result', s !== null && (await page.getByTestId('search-outcome').innerText()).length > 10, s?.analytical_outcome)
    const rows = page.locator('.layout-table tbody tr')
    check('one table row per returned layout', await rows.count() === s.layouts.length, `${s.layouts.length} layouts`)
    const values = s.layouts.map(l => s.metrics.find(x => x.layout_id === l.layout.layout_id && x.metric_id === 'additional_shade' && x.case_id === primary)).filter(Boolean).map(x => fmt(x.value))
    check('each layout\'s shade on screen equals its stored metric', values.every(v => panel.includes(`${v} m²·h`)), values.join(', '))
    const canvas = page.locator('.site-panel .scene-canvas canvas').first()
    const before = hash(await canvas.evaluate(el => el.toDataURL('image/png')))
    await page.locator('.layout-table tbody tr').last().getByRole('button').first().click()
    await page.waitForTimeout(400)
    check('selecting a layout highlights its placements in the 3D view', before !== hash(await canvas.evaluate(el => el.toDataURL('image/png'))))
    await shot(page, '02-search')

    // Move to candidate-3 by keyboard, accept and recompute.
    await page.locator('.scene-wrap').first().focus()
    await page.keyboard.press('ArrowRight')
    await page.waitForTimeout(200)
    check('arrow key steps to the next catalogue position', await page.getByRole('radio', { name: /candidate-3/ }).isChecked())
    check('the move marks the result stale', /STALE/.test(await page.locator('.currentness strong').first().innerText()))
    await waitJob(page, page.getByRole('button', { name: /Accept changes/ }))
    const h2 = await head()
    const layout = await backend('GET', `/layouts/${h2.input.proposed_layout_ref.layout_id}?revision=${h2.input.proposed_layout_ref.revision}`)
    check('accepted layout carries candidate-3 identity and position', layout.placements[0].candidate_id === 'candidate-3' && layout.placements[0].location_id === 'location-3' && layout.placements[0].position_enu_m[0] === 2, JSON.stringify(layout.placements[0]))
    r = await latest('evaluate_layout')
    m = r?.metrics.find(x => x.metric_id === 'additional_shade' && x.case_id === primary)
    if (m) await page.waitForFunction(v => document.querySelector('[data-testid=metric-value]')?.textContent === v, fmt(m.value), { timeout: 15000 }).catch(() => {})
    check('recomputed metric for candidate-3 equals the stored Result and is CURRENT', m && (await page.getByTestId('metric-value').innerText()) === fmt(m.value) && /CURRENT\b/.test(await page.locator('.currentness strong').first().innerText()), m ? `${m.value}` : 'no result')
    await shot(page, '03-candidate-3')

    // Backend location comparison: draft candidate-2 vs accepted candidate-3.
    await page.getByRole('radio', { name: /candidate-2/ }).check()
    await nav.getByRole('button', { name: /Compare/ }).click()
    await page.getByRole('button', { name: /Compare draft position on the backend/ }).click()
    await page.getByTestId('backend-delta').first().waitFor({ timeout: 60000 })
    await page.waitForTimeout(300)
    const c = await latest('compare_locations')
    const cmpText = await page.locator('.compare-card', { hasText: 'BACKEND COMPARISON' }).innerText()
    check('backend location comparison rendered from its ComparisonMetadata', c?.comparison && cmpText.includes(`Mode: ${c.comparison.mode}`) && !/unresolved/.test(cmpText), c ? `${c.comparison.mode}, ${c.comparison.deltas.length} deltas` : 'no result')
    const winter = await page.getByTestId('winter-status').innerText()
    check('winter trade-off is reported from the winter case, not "not evaluated"', !/Not evaluated/.test(winter) && /winter/i.test(winter), winter.replace(/\s+/g, ' ').slice(0, 140))
    await shot(page, '04-compare')
    await nav.getByRole('button', { name: /Planning studio/ }).click()
    await page.getByRole('button', { name: 'Discard draft' }).click()

    // Agent-host proposal -> backend scenario comparison (fixed layout), never accepted.
    const base = await head()
    const prepared = await backend('POST', '/operations', {
      request_id: `physical-proposal-${Date.now()}`, operation: 'prepare_scenario',
      arguments: { base_scenario_ref: { scenario_id: base.scenario_id, revision: base.revision, scope: 'accepted' }, proposed_edits: { ...base.input, constraints: { ...base.input.constraints, budget_pence: 30000, max_tree_count: 3 } } },
    }, { 'X-Canopy-Scenario-Id': base.scenario_id, 'X-Canopy-Scenario-Revision': String(base.revision) })
    await page.getByLabel('Proposal scenario id').fill(prepared.scenario_id)
    await page.getByLabel('Proposal revision').fill(String(prepared.revision))
    await page.getByRole('button', { name: 'Load' }).click()
    await page.getByTestId('proposal-review').waitFor()
    await waitJob(page, page.getByRole('button', { name: /Compare with accepted on the backend/ }))
    await page.waitForTimeout(800)
    const sc = await latest('compare_scenarios')
    check('backend scenario comparison completed without accepting the proposal', sc?.comparison && (await head()).revision === base.revision, sc ? `${sc.comparison.mode}; changed ${sc.comparison.changed_inputs.join(', ')}` : 'no result')
    await page.getByRole('button', { name: /Reject/ }).click()

    // Review pack export equals stored records.
    await nav.getByRole('button', { name: /Review pack/ }).click()
    const dl = page.waitForEvent('download')
    await page.getByRole('button', { name: /Download review pack/ }).click()
    const pack = JSON.parse(readFileSync(await (await dl).path(), 'utf8'))
    const stored = await backend('GET', `/results/${pack.result.run_id}`)
    check('exported pack copies the stored physical Result unchanged', JSON.stringify(pack.result) === JSON.stringify(stored))
    await shot(page, '05-report')
    check('no page errors', errors.length === 0, errors.join('; '))
  } catch (e) {
    check('script completed', false, String(e).slice(0, 300))
  } finally {
    await browser.close()
  }
  // Demo-resolution captures.
  const hd = await chromium.launch({ executablePath: browserPath, headless: true, args: ['--no-sandbox', '--no-proxy-server'] })
  try {
    const p = await hd.newPage({ viewport: { width: 1920, height: 1080 } })
    await p.goto(url)
    await p.getByText('Local backend connected').waitFor({ timeout: 20000 })
    await p.waitForTimeout(700)
    const n = p.getByRole('navigation', { name: 'Main navigation' })
    for (const [name, label] of [['10-hd-studio', /Planning studio/], ['11-hd-compare', /Compare/], ['12-hd-report', /Review pack/]]) {
      await n.getByRole('button', { name: label }).click()
      await p.waitForTimeout(500)
      await p.screenshot({ path: join(evidenceDir, `${name}.png`) })
    }
  } finally { await hd.close() }
  writeFileSync(join(evidenceDir, 'physical-check.json'), JSON.stringify({ url, api, checks: log }, null, 2))
})()
