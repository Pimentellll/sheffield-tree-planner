// Integrated UI check against a real running backend (scripts/serve_reference.py) and Vite dev server.
// Every number asserted here comes from the backend's actual jobs; nothing is mocked.
//
//   CANOPY_DEV_WORKSPACE=<launcher workspace>  enables the controlled asset-corruption failure step
//   CANOPY_OFFLINE=1                            checks the not-connected state instead (no backend)
const { chromium } = require('playwright-core')
const { createHash } = require('node:crypto')
const { mkdirSync, readFileSync, writeFileSync, existsSync } = require('node:fs')
const { join } = require('node:path')

const defaultBrowser = process.platform === 'win32'
  ? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
  : ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(existsSync)
const browserPath = process.env.CANOPY_BROWSER || defaultBrowser
const url = process.env.CANOPY_URL || 'http://127.0.0.1:5173/'
const workspace = process.env.CANOPY_DEV_WORKSPACE
const offline = process.env.CANOPY_OFFLINE === '1'
const api = (process.env.CANOPY_API || 'http://127.0.0.1:8765').replace(/\/$/, '')
// Out-of-band client: another accepted change, or the planning agent's host, talking to the same backend.
async function backend(method, path, body, headers = {}) {
  const response = await fetch(api + '/api/v1' + path, {
    method, headers: { Origin: new URL(api).origin, ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers },
    body: body ? JSON.stringify(body) : undefined,
  })
  const json = await response.json()
  if (!response.ok) throw new Error(`${method} ${path} -> ${response.status} ${JSON.stringify(json)}`)
  return { json, etag: response.headers.get('etag') }
}
async function head() {
  const session = await (await fetch(new URL('/canopy-dev-session.json', url))).json()
  let rev = session.scenario_ref.revision
  const id = session.scenario_ref.scenario_id
  for (;;) {
    const r = await fetch(`${api}/api/v1/scenarios/${id}?revision=${rev + 1}`)
    if (r.status !== 200) break
    rev += 1
  }
  return (await backend('GET', `/scenarios/${id}?revision=${rev}`)).json
}
const currentLabel = page => page.locator('.currentness strong').textContent()
const evidenceDir = join(__dirname, '..', 'artifacts')
mkdirSync(evidenceDir, { recursive: true })
const hash = bytes => createHash('sha256').update(bytes).digest('hex')
const log = []
const check = (name, ok, detail = '') => { log.push({ name, ok: Boolean(ok), detail }); if (!ok) process.exitCode = 1; console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`) }

async function launch(width, height) {
  const browser = await chromium.launch({ executablePath: browserPath, headless: true, args: ['--no-sandbox', '--no-proxy-server'] })
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 })
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  return { browser, page, errors }
}

const panel = page => page.locator('.detail-panel')
const metric = page => page.getByTestId('metric-value')
const shot = (page, name) => page.screenshot({ path: join(evidenceDir, `${name}.png`), fullPage: true })

async function evaluateAndWait(page) {
  const jobText = () => page.evaluate(() => document.querySelector('.job-status span')?.textContent ?? '')
  const before = await jobText()
  await page.getByRole('button', { name: /evaluate/i }).first().click()
  await page.waitForFunction(prev => {
    const status = document.querySelector('.job-status strong')?.textContent ?? ''
    const job = document.querySelector('.job-status span')?.textContent ?? ''
    return (job !== prev && /Completed|Failed|Cancelled/.test(status)) || document.querySelector('.error-box[role=alert]') !== null
  }, before, { timeout: 20000 })
  await page.waitForTimeout(400)
}

async function online() {
  const { browser, page, errors } = await launch(1440, 1000)
  try {
    await page.goto(url)
    await page.getByText('Local backend connected').waitFor({ timeout: 20000 })
    check('connects to the local backend', true)
    const text = await panel(page).innerText()
    check('site geometry bytes verified against SiteBundle hash', /Verified · sha256/.test(text))
    check('synthetic site is labelled as not Sheffield', /Synthetic test \(not Sheffield\)/.test(text))
    check('identity analysis_to_viewer is reported, not hidden', /Identity in SiteBundle/.test(text))
    await shot(page, '01-loaded')

    // Camera keyboard alternative still changes the canvas.
    const canvas = page.locator('.scene-canvas canvas')
    const before = hash(await canvas.screenshot())
    await page.getByRole('button', { name: 'Orbit camera left' }).click()
    await page.waitForTimeout(400)
    check('camera orbit control changes the view', before !== hash(await canvas.screenshot()))
    await page.getByRole('button', { name: 'Reset view' }).click()

    // 1. Positive evaluation at the seeded position.
    await evaluateAndWait(page)
    await metric(page).waitFor()
    const positive = await metric(page).textContent()
    check('positive evaluation returns the backend value 2 m²·h', positive === '2', `got ${positive}`)
    check('positive result is CURRENT', /CURRENT\b/.test(await page.locator('.currentness strong').textContent()))
    await shot(page, '02-positive-current')

    // 2. Editing immediately makes the shown number stale (before any save).
    const east = page.getByRole('spinbutton').first()
    await east.fill('20')
    await east.press('Enter')
    await page.waitForTimeout(150)
    const stale = await page.locator('.currentness strong').textContent()
    check('unsaved move marks the result stale immediately', /STALE/.test(stale), stale)
    check('stale number is visibly struck through', await page.locator('.metric-stale').count() === 1)
    const beforeFind = hash(await canvas.screenshot())
    await page.getByRole('button', { name: 'Find tree' }).click()
    await page.waitForTimeout(400)
    check('Find tree recentres the camera on the moved tree', beforeFind !== hash(await canvas.screenshot()))
    await shot(page, '03-edit-stale')

    // 3. Save + evaluate: valid zero, and the old result is superseded.
    await evaluateAndWait(page)
    await page.waitForFunction(() => document.querySelector('[data-testid=metric-value]')?.textContent === '0', null, { timeout: 20000 })
    check('moved tree returns a valid zero from the backend', true)
    check('valid-zero explanation shown', await page.getByText(/Valid zero/).count() === 1)
    check('zero result is CURRENT at the new revision', /CURRENT\b/.test(await page.locator('.currentness strong').textContent()))
    const history = await page.locator('.run-history').innerText()
    check('earlier revision result is listed as SUPERSEDED', /rev 1 \| 2 m²·h \| SUPERSEDED/.test(history.replace(/\n/g, ' | ')) , history.replace(/\n/g, ' | '))
    await shot(page, '04-zero-current-history')

    // 4. Keyboard editing on the focused scene: ArrowRight moves 0.1 m east.
    await page.locator('.scene-wrap').focus()
    await page.keyboard.press('ArrowRight')
    await page.waitForTimeout(150)
    check('arrow key moves the tree 0.1 m east', (await east.inputValue()) === '20.1', await east.inputValue())
    await page.locator('.scene-wrap').focus()
    await page.keyboard.press('ArrowLeft')
    await page.waitForTimeout(150)
    check('moving back to the evaluated position clears staleness', /CURRENT\b/.test(await page.locator('.currentness strong').textContent()))

    // 5. Controlled failure: corrupt only the launcher's generated asset, evaluate, then restore.
    if (workspace) {
      const asset = join(workspace, 'runtime', 'inputs', 'synthetic-reference.json')
      const original = readFileSync(asset)
      try {
        writeFileSync(asset, Buffer.concat([original, Buffer.from('\n')]))
        await evaluateAndWait(page)
        const status = await page.locator('.job-status strong').textContent()
        const rejected = await page.locator('.error-box[role=alert]').count() ? await page.locator('.error-box[role=alert]').textContent() : null
        const jobFailed = status === 'Failed'
        check('changed input asset fails closed (rejected at admission or failed job)', Boolean(rejected) || jobFailed, rejected ? `submission rejected: ${rejected}` : `job ${status}`)
        const card = await page.locator('.result-section').innerText()
        check('no new number is produced from the changed asset', (await metric(page).textContent()) === '0' && !/Live computation[\s\S]*rev 3/.test(card))
        await shot(page, '05-failure')
      } finally {
        writeFileSync(asset, original)
      }
      await evaluateAndWait(page)
      check('restored asset recovers a CURRENT result', /CURRENT\b/.test(await page.locator('.currentness strong').textContent()) && (await metric(page).textContent()) === '0')
      await shot(page, '06-recovered')
    } else {
      check('failure step skipped (CANOPY_DEV_WORKSPACE not set)', true)
    }
    await requirementsFlow(page)
    check('no page errors', errors.length === 0, errors.join('; '))
  } finally { await browser.close() }

  // Narrow layout with the same live backend.
  const narrow = await launch(390, 844)
  try {
    await narrow.page.goto(url)
    await narrow.page.getByText('Local backend connected').waitFor({ timeout: 20000 })
    await narrow.page.waitForTimeout(500)
    const g = await narrow.page.evaluate(() => ({ viewport: innerWidth, scroll: document.documentElement.scrollWidth }))
    check('no horizontal overflow at 390 px', g.scroll <= g.viewport, JSON.stringify(g))
    await shot(narrow.page, '07-narrow')
    check('no page errors (narrow)', narrow.errors.length === 0, narrow.errors.join('; '))
  } finally { await narrow.browser.close() }
}

// STP-021: requirement drafts, human acceptance, recompute, refused concurrent edit, proposal review.
async function requirementsFlow(page) {
  const budget = page.getByLabel('Upfront budget in pounds')
  const before = await head()
  await budget.fill('80')
  await budget.press('Enter')
  await page.waitForTimeout(150)
  check('budget edit shows a DRAFT · NOT ACCEPTED badge', await page.getByTestId('draft-badge').count() === 1)
  check('draft change set names constraints.budget_pence', /constraints\.budget_pence: 10000 → 8000/.test(await page.getByTestId('draft-changes').innerText()))
  check('requirement draft marks the shown result stale', /STALE/.test(await currentLabel(page)))
  check('nothing was written before acceptance', (await head()).revision === before.revision)
  await page.getByRole('button', { name: 'Discard draft' }).click()
  await page.waitForTimeout(150)
  check('discarding the draft restores CURRENT', /CURRENT\b/.test(await currentLabel(page)) && await page.getByTestId('draft-badge').count() === 0)

  await budget.fill('80')
  await budget.press('Enter')
  await page.getByLabel('Maximum tree count (blank for no limit)').fill('1')
  await page.getByLabel('Maximum tree count (blank for no limit)').press('Enter')
  await evaluateAndWait(page)
  const accepted = await head()
  check('accepting creates the next accepted revision with only those constraints changed',
    accepted.revision === before.revision + 1 && accepted.input.constraints.budget_pence === 8000 && accepted.input.constraints.max_tree_count === 1 &&
    JSON.stringify(accepted.input.proposed_layout_ref) === JSON.stringify(before.input.proposed_layout_ref),
    `rev ${accepted.revision}, budget ${accepted.input.constraints.budget_pence}, max ${accepted.input.constraints.max_tree_count}`)
  check('acceptance triggers a real recomputation that is CURRENT', /CURRENT\b/.test(await currentLabel(page)) &&
    (await page.locator('.result-section').innerText()).includes(`${accepted.revision} (accepted)`))
  await shot(page, '08-requirements-accepted')

  // Refused edit: someone else accepts a change first; our acceptance must not be applied.
  const other = { ...accepted.input, constraints: { ...accepted.input.constraints, budget_pence: 7000 } }
  await backend('PUT', `/scenarios/${accepted.scenario_id}`, other, { 'If-Match': `"${accepted.revision}"` })
  await budget.fill('60')
  await budget.press('Enter')
  await page.getByRole('button', { name: /Accept changes/ }).click()
  await page.locator('.error-box[role=alert]', { hasText: 'newer accepted revision' }).waitFor({ timeout: 10000 })
  const latest = await head()
  const errorText = await page.locator('.error-box[role=alert]').textContent()
  check('concurrent acceptance refuses our stale write (REVISION_CONFLICT)', /REVISION_CONFLICT/.test(errorText) && latest.input.constraints.budget_pence === 7000, `head budget ${latest.input.constraints.budget_pence}`)
  check('after the refusal the newer head is loaded and the old result is SUPERSEDED, not current',
    /newer accepted revision/.test(errorText) && /SUPERSEDED/.test(await currentLabel(page)))
  check('the refused draft is kept for re-acceptance', /constraints\.budget_pence: 7000 → 6000/.test(await page.getByTestId('draft-changes').innerText()))
  await shot(page, '09-refused-edit')
  await page.getByRole('button', { name: 'Discard draft' }).click()

  // Proposal from the agent's host surface (real dispatcher, scoped by headers), then human acceptance.
  const base = await head()
  const edits = { ...base.input, constraints: { ...base.input.constraints, budget_pence: 5000 } }
  const prepared = (await backend('POST', '/operations', {
    request_id: `test-proposal-${Date.now()}`, operation: 'prepare_scenario',
    arguments: { base_scenario_ref: { scenario_id: base.scenario_id, revision: base.revision, scope: 'accepted' }, proposed_edits: edits },
  }, { 'X-Canopy-Scenario-Id': base.scenario_id, 'X-Canopy-Scenario-Revision': String(base.revision) })).json
  check('backend prepared a hypothetical proposal (not accepted)', prepared.scope === 'hypothetical' && (await head()).revision === base.revision)
  await page.getByLabel('Proposal scenario id').fill(prepared.scenario_id)
  await page.getByLabel('Proposal revision').fill(String(prepared.revision))
  await page.getByRole('button', { name: 'Load' }).click()
  await page.getByTestId('proposal-review').waitFor()
  check('proposal diff shows the proposed budget change', /constraints\.budget_pence: 7000 → 5000/.test(await page.getByTestId('proposal-review').innerText()))
  await shot(page, '10-proposal-review')
  const jobBefore = await page.evaluate(() => document.querySelector('.job-status span')?.textContent ?? '')
  await page.getByRole('button', { name: /Accept proposal/ }).click()
  await page.waitForFunction(prev => {
    const job = document.querySelector('.job-status span')?.textContent ?? ''
    return job !== prev && /Completed|Failed|Cancelled/.test(document.querySelector('.job-status strong')?.textContent ?? '')
  }, jobBefore, { timeout: 20000 })
  await page.waitForTimeout(400)
  const afterAccept = await head()
  check('human acceptance of the proposal creates the next accepted revision', afterAccept.revision === base.revision + 1 && afterAccept.input.constraints.budget_pence === 5000)
  check('accepted proposal is recomputed and CURRENT', /CURRENT\b/.test(await currentLabel(page)))
  // A second acceptance of the same proposal is refused by the backend.
  let refused = false
  try { await backend('POST', '/scenarios/accept', { scenario_id: prepared.scenario_id, revision: prepared.revision, scope: 'hypothetical' }, { 'If-Match': `"${afterAccept.revision}"` }) } catch { refused = true }
  check('the same proposal cannot be accepted twice', refused)
  await shot(page, '11-proposal-accepted')
}

async function offlineCheck() {
  const { browser, page, errors } = await launch(1440, 900)
  try {
    await page.goto(url)
    await page.getByText('Backend not connected').waitFor({ timeout: 20000 })
    check('offline state is explicit', true)
    check('no metric is shown without a backend', await metric(page).count() === 0)
    check('evaluate is disabled offline', await page.getByRole('button', { name: /Evaluate planting/ }).isDisabled())
    await shot(page, '00-offline')
    check('no page errors', errors.length === 0, errors.join('; '))
  } finally { await browser.close() }
}

;(offline ? offlineCheck() : online())
  .catch(error => { console.error(error); process.exitCode = 1 })
  .finally(() => writeFileSync(join(evidenceDir, offline ? 'offline-check.json' : 'browser-check.json'), JSON.stringify({ url, offline, checks: log }, null, 2)))
// Note: run against a freshly started scripts/serve_reference.py workspace; the checks assume the seeded revision 1.
