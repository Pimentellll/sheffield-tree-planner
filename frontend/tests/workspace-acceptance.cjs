// Manual-workspace acceptance (#17, #25) against a FRESH synthetic physical session
// (scripts/serve_physical.py --winter) and the Vite dev server. These are manual/synthetic UI checks,
// not model or real-site claims.
//
// Every assertion compares the screen with the backend's own stored record (Job, Result, Selection,
// SiteBundle, Scenario) read over the API in the same run; nothing is hard-coded and no response is
// intercepted or altered. A display state this runtime cannot produce is reported as NOT-REACHABLE with
// the code path that explains why and the unit tests that cover it; it is never simulated here.
//
// A queued job is obtained honestly: the test submits real search jobs on hypothetical scenarios, so the
// single background worker is busy and the UI's own job waits in the queue long enough to be cancelled.
//
//   CANOPY_URL=http://127.0.0.1:5178/ CANOPY_API=http://127.0.0.1:8768 npm run test:acceptance
const { chromium } = require('playwright-core')
const { mkdirSync, writeFileSync, existsSync } = require('node:fs')
const { join } = require('node:path')

const browserPath = process.env.CANOPY_BROWSER || (process.platform === 'win32'
  ? 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
  : ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(existsSync))
const url = process.env.CANOPY_URL || 'http://127.0.0.1:5173/'
const api = (process.env.CANOPY_API || 'http://127.0.0.1:8765').replace(/\/$/, '')
const evidenceDir = join(__dirname, '..', 'artifacts', 'acceptance')
mkdirSync(evidenceDir, { recursive: true })
const DESKTOP = { width: 1920, height: 1080 }
const NARROW = { width: 390, height: 844 }
const FLOOD = Number(process.env.CANOPY_FLOOD || 45)

const log = []
const line = (status, name, detail) => { log.push({ status, name, detail }); console.log(`${status} ${name}${detail ? ` — ${detail}` : ''}`) }
const check = (name, ok, detail = '') => { if (!ok) process.exitCode = 1; line(ok ? 'PASS' : 'FAIL', name, detail) }
const notReachable = (name, reason) => line('NOT-REACHABLE', name, reason)
const fmt = v => String(Number(v.toFixed(6)))
const short = id => `${id.slice(0, 8)}…`

async function raw(method, path, body, headers = {}) {
  const r = await fetch(api + '/api/v1' + path, { method, headers: { Origin: new URL(api).origin, ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers }, body: body ? JSON.stringify(body) : undefined })
  return { status: r.status, json: await r.json() }
}
async function backend(method, path, body, headers) {
  const r = await raw(method, path, body, headers)
  if (r.status >= 300) throw new Error(`${method} ${path} -> ${r.status} ${JSON.stringify(r.json)}`)
  return r.json
}
async function head() {
  const s = await (await fetch(new URL('/canopy-dev-session.json', url))).json()
  let rev = s.scenario_ref.revision
  while ((await fetch(`${api}/api/v1/scenarios/${s.scenario_ref.scenario_id}?revision=${rev + 1}`)).status === 200) rev += 1
  return backend('GET', `/scenarios/${s.scenario_ref.scenario_id}?revision=${rev}`)
}
const selections = h => backend('GET', `/scenarios/${h.scenario_id}/selections?revision=${h.revision}&scope=accepted`)
const prepare = (h, constraints) => raw('POST', '/operations', {
  request_id: `acceptance-${Date.now()}-${Math.random().toString(16).slice(2)}`, operation: 'prepare_scenario',
  arguments: { base_scenario_ref: { scenario_id: h.scenario_id, revision: h.revision, scope: 'accepted' }, proposed_edits: { ...h.input, constraints: { ...h.input.constraints, ...constraints } } },
}, { 'X-Canopy-Scenario-Id': h.scenario_id, 'X-Canopy-Scenario-Revision': String(h.revision) })

/** Hypothetical scenarios (distinct budgets, so distinct inputs) whose real search jobs will occupy the worker. */
async function prepareFlood(h, salt) {
  const out = []
  for (let i = 0; i < FLOOD; i += 9) {
    const batch = await Promise.all(Array.from({ length: Math.min(9, FLOOD - i) }, (_, k) => prepare(h, { budget_pence: h.input.constraints.budget_pence + salt + i + k + 1 })))
    for (const r of batch) { if (r.status >= 300) throw new Error(`prepare_scenario -> ${r.status} ${JSON.stringify(r.json)}`); out.push(r.json) }
  }
  return out
}
const submitFlood = prepared => Promise.all(prepared.map(p => backend('POST', '/jobs', {
  request_id: `acceptance-flood-${Date.now()}-${Math.random().toString(16).slice(2)}`, operation: 'search_layouts',
  scenario_ref: { scenario_id: p.scenario_id, revision: p.revision, scope: 'hypothetical' }, arguments: {},
})))
/** Cancel whatever of the flood is still queued and wait until the worker is idle again. */
async function drainFlood(jobs) {
  await Promise.all(jobs.map(j => raw('POST', `/jobs/${j.job_id}/cancel`)))
  for (let i = 0; i < 100; i++) {
    const states = await Promise.all(jobs.map(async j => (await backend('GET', `/jobs/${j.job_id}`)).status))
    if (states.every(s => ['completed', 'failed', 'cancelled'].includes(s))) return states
    await new Promise(r => setTimeout(r, 200))
  }
  throw new Error('flood jobs did not reach a terminal state')
}

const jobLabel = page => page.locator('.job-status strong').first().innerText().catch(() => '')
async function waitTerminal(page, previousJobLine) {
  await page.waitForFunction(prev => {
    const jobLine = document.querySelector('.job-status span')?.textContent ?? ''
    return (jobLine !== prev && /Completed|Failed|Cancelled/.test(document.querySelector('.job-status strong')?.textContent ?? '')) || document.querySelector('.error-box[role=alert]')
  }, previousJobLine, { timeout: 60000 })
  await page.waitForTimeout(600)
}
const jobLine = page => page.evaluate(() => document.querySelector('.job-status span')?.textContent ?? '')
async function runToEnd(page, button) {
  const before = await jobLine(page)
  await button.click()
  await waitTerminal(page, before)
}
/** Click the action, then the UI's own Cancel button while the job is still queued behind the flood. */
async function runAndCancel(page, button) {
  const before = await jobLine(page)
  await button.click()
  const cancel = page.getByRole('button', { name: 'Cancel job' })
  await cancel.waitFor({ timeout: 15000 })
  await cancel.click()
  await waitTerminal(page, before)
}
async function shots(page, name) {
  await page.screenshot({ path: join(evidenceDir, `${name}-1920x1080.png`) })
  await page.screenshot({ path: join(evidenceDir, `${name}-1920-full.png`), fullPage: true })
  await page.setViewportSize(NARROW)
  await page.waitForTimeout(500)
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  await page.screenshot({ path: join(evidenceDir, `${name}-390.png`), fullPage: true })
  await page.setViewportSize(DESKTOP)
  await page.waitForTimeout(400)
  return overflow
}
const resultText = page => page.locator('.result-section').innerText()
const currentness = page => page.locator('.result-section .currentness strong').first().innerText()
const headerText = async page => (await page.locator('body').innerText()).match(/REV \d+ · (RESULT CURRENT|NO CURRENT RESULT|NO RESULT YET)[^\n]*/)?.[0] ?? '(no header status found)'

;(async () => {
  const browser = await chromium.launch({ executablePath: browserPath, headless: true, args: ['--no-sandbox', '--no-proxy-server'] })
  const page = await browser.newPage({ viewport: DESKTOP })
  const errors = []
  page.on('pageerror', e => errors.push(e.message))
  let session = null
  try {
    session = await (await fetch(new URL('/canopy-dev-session.json', url))).json()
    const health = await backend('GET', '/health')
    const h0 = await head()
    const sel0 = await selections(h0)
    const fresh = h0.revision === 1 && ['evaluation', 'search', 'comparison'].every(s => sel0[s].selection === null || sel0[s].selection === undefined)
    check('session is fresh (revision 1, no job selected yet)', fresh, `scenario ${short(h0.scenario_id)} rev ${h0.revision}, started ${session.started_at_utc}`)
    const site = await backend('GET', `/sites/${h0.input.site_id}?scene_revision=${h0.input.scene_revision}&semantic_revision=${h0.input.semantic_revision}`).catch(async () => null)

    await page.goto(url)
    await page.getByText('Local backend connected').waitFor({ timeout: 20000 })
    await page.waitForTimeout(800)

    // ---- (3) provisional display -------------------------------------------------------------
    if (site) {
      const provisional = site.candidate_catalogue.filter(c => c.plantability_status === 'provisional')
      const labels = await page.getByRole('radio').evaluateAll(els => els.map(e => e.closest('label')?.textContent ?? ''))
      const shown = provisional.every(c => labels.some(l => l.includes(c.candidate_id) && /provisional/.test(l)))
      const others = site.candidate_catalogue.filter(c => c.plantability_status !== 'provisional').every(c => !labels.some(l => l.includes(c.candidate_id) && /provisional/.test(l)))
      check('(3) provisional: every catalogue position the SiteBundle marks provisional is labelled provisional, and no other', provisional.length > 0 && shown && others,
        `SiteBundle ${site.site_id}: ${site.candidate_catalogue.map(c => `${c.candidate_id}=${c.plantability_status}`).join(', ')}`)
      const identity = JSON.stringify(site.analysis_to_viewer) === JSON.stringify([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
      const panel = await page.locator('body').innerText()
      check('(3) provisional: viewer frame row states the provisional transform is used when the SiteBundle transform is identity', identity ? /Identity in SiteBundle — provisional used/.test(panel) : !/Identity in SiteBundle — provisional used/.test(panel),
        `SiteBundle analysis_to_viewer is ${identity ? 'identity' : 'not identity'}`)
    } else {
      check('(3) provisional: SiteBundle readable from the backend', false, 'GET /sites failed')
    }
    await shots(page, '01-loaded-provisional')

    // ---- (5) exclusion edit path ---------------------------------------------------------------
    const excl = site ? site.exclusions.length : null
    await page.getByRole('button', { name: 'Edit scenario' }).click()
    await page.getByLabel('Upfront budget in pounds').waitFor()
    const editor = await page.locator('section.ed').innerText()
    const boxes = await page.locator('section.ed input[type=checkbox]').count()
    check('(5) exclusion editor offers exactly the SiteBundle\'s exclusion regions', excl !== null && boxes === excl && (excl > 0 || /defines no exclusion regions, so none can be selected/.test(editor)),
      `SiteBundle exclusions: ${excl}; checkboxes on screen: ${boxes}; accepted excluded_region_ids: ${JSON.stringify(h0.input.constraints.excluded_region_ids)}`)
    const refused = await prepare(h0, { excluded_region_ids: ['acceptance-no-such-region'] })
    check('(5) backend refuses an exclusion id the SiteBundle does not define (so the UI offering none is the truthful state)', refused.status === 422, `prepare_scenario -> ${refused.status} ${refused.json.code ?? ''}`)
    if (excl === 0) {
      notReachable('(5) exclusion EDIT (toggle a region, accept, recompute)', 'the synthetic physical SiteBundle is seeded with exclusions=[] (backend/src/tree_planner/evaluators/physical_seed.py) and the backend rejects any other id with 422, so there is no region to toggle; the editor shows "defines no exclusion regions" instead (frontend/src/panels/Requirements.tsx). Covered by unit tests: evaluation.test.ts (validateRequirements and sameRequirements with excludedRegionIds; buildCommit). The same draft -> accept -> recompute path is exercised below with a budget edit.')
    }
    await shots(page, '02-exclusion-editor')
    await page.getByRole('button', { name: /Close editor|Close scenario editor/ }).first().click()

    // ---- live evaluation, then a repeat on the same revision ((1) cached, (4) fixture) ---------
    await runToEnd(page, page.getByRole('button', { name: /Evaluate planting/ }))
    let sel = await selections(h0)
    const jobA = sel.evaluation.current_job
    const resA = await backend('GET', `/results/${jobA.run_id}`)
    const primary = h0.input.objective.primary_case_id
    const mA = resA.metrics.find(x => x.metric_id === 'additional_shade' && x.case_id === primary && x.target_id === null) ?? resA.metrics.find(x => x.metric_id === 'additional_shade' && x.case_id === primary)
    check('baseline: live evaluation shown CURRENT with the stored metric', (await page.getByTestId('metric-value').innerText()) === fmt(mA.value) && /^CURRENT$/.test(await currentness(page)),
      `job ${short(jobA.job_id)} run ${short(jobA.run_id)} delivery=${jobA.delivery.execution_mode} value=${mA.value} ${mA.unit}`)

    await runToEnd(page, page.getByRole('button', { name: /Evaluate planting/ }))
    sel = await selections(h0)
    const jobB = sel.evaluation.current_job
    const resB = await backend('GET', `/results/${jobB.run_id}`)
    const BADGE = { live: 'COMPUTED · LIVE', cached: 'CACHED RESULT', recorded: 'RECORDED, NOT RECOMPUTED', fixture: 'FIXTURE · NOT COMPUTED' }
    const MODE = { live: 'Live computation', cached: 'Cached result (exact same inputs)', recorded: 'Recorded result, not recomputed', fixture: 'Fixture, not a computation' }
    let text = await resultText(page)
    const delivered = jobB.delivery.execution_mode
    check('repeat evaluation on the same revision: mode badge and Mode row equal the backend Job.delivery.execution_mode, never another mode',
      jobB.job_id !== jobA.job_id && text.includes(BADGE[delivered]) && text.includes(MODE[delivered]) && Object.keys(BADGE).filter(k => k !== delivered).every(k => !text.includes(BADGE[k])),
      `job ${short(jobB.job_id)} delivery=${delivered}, Result.provenance.execution_mode=${resB.provenance.execution_mode}, run ${short(jobB.run_id)} (${jobB.run_id === jobA.run_id ? 'same run as first' : 'new run'})`)
    if (delivered === 'cached') {
      check('(1) cached: cache-delivered job states its original mode', text.includes(`originally ${MODE[resB.provenance.execution_mode].toLowerCase()}`), `delivery=cached, provenance=${resB.provenance.execution_mode}`)
    } else {
      notReachable('(1) cached result display', `an identical repeat request on the same revision was delivered "${delivered}" as ${jobB.run_id === jobA.run_id ? 'the same' : 'a new'} run: JobStore.deliver_cached (backend/src/tree_planner/jobs/__init__.py) has no caller in the HTTP/background-worker runtime (physical_demo.py records this phase as "repeat-live"; cache delivery is proven only at controller level in backend/tests/jobs/test_jobs.py and backend/tests/evaluators/test_physical_runtime.py). UI labels covered by unit tests: shell.test.ts (provenanceItems / MODE_BADGE), agentEvidence.test.ts.`)
    }
    const modes = new Set([jobA.delivery.execution_mode, jobB.delivery.execution_mode, resA.provenance.execution_mode, resB.provenance.execution_mode])
    if (modes.has('fixture')) check('(4) fixture: fixture badge shown', text.includes(BADGE.fixture))
    else notReachable('(4) fixture display', `no Job or Result of this runtime carries execution_mode "fixture" (observed: ${[...modes].join(', ')}); "fixture" exists only as a contract literal (backend/src/tree_planner/contracts/results.py ExecutionMode) and no evaluator registered by create_physical_runtime emits it. The banner on screen says the site is synthetic. UI label covered by unit tests: shell.test.ts (MODE_BADGE / provenanceItems), evaluation.ts EXECUTION_MODE_LABEL via agentEvidence.test.ts.`)
    const notice = await page.getByTestId('site-notice').innerText()
    check('(4) synthetic-site disclosure is shown and matches SiteBundle.site_kind', site && site.site_kind === 'synthetic_test' && /not Sheffield/.test(notice), `site_kind=${site?.site_kind}`)
    await shots(page, '03-repeat-evaluation-live')

    // ---- (2) cancelled + (6) newer cancelled selection on the SAME revision --------------------
    let prepared = await prepareFlood(h0, 0)
    let flood = await submitFlood(prepared)
    await runAndCancel(page, page.getByRole('button', { name: /Evaluate planting/ }))
    sel = await selections(h0)
    const cancelledId = sel.evaluation.selection?.accepted_job_id
    const jobC = cancelledId ? await backend('GET', `/jobs/${cancelledId}`) : null
    const reached = jobC && jobC.status === 'cancelled' && jobC.job_id !== jobB.job_id
    if (!reached) {
      notReachable('(2) cancelled job display / (6) same-revision newer cancelled selection', `the UI job finished as "${jobC?.status}" before the Cancel click landed although ${FLOOD} real search jobs were queued ahead of it (raise CANOPY_FLOOD)`)
    } else {
      text = await resultText(page)
      const status = await page.locator('.job-status').first().innerText()
      check('(2) cancelled: job panel shows Cancelled with no stored result, matching the backend Job', /Cancelled/.test(await jobLabel(page)) && /No result was stored/.test(status) && status.includes(jobC.job_id.slice(0, 8)) && jobC.run_id === null,
        `job ${short(jobC.job_id)} status=${jobC.status} run_id=${jobC.run_id} error=${jobC.error?.code} selection_seq=${jobC.selection_seq}`)
      check('(6) backend selection for this revision now points at the cancelled job and exposes no current job', sel.evaluation.current_job === null && sel.evaluation.selection.accepted_job_id === jobC.job_id,
        `selections.evaluation: accepted_job_id=${short(sel.evaluation.selection.accepted_job_id)} current_job=${JSON.stringify(sel.evaluation.current_job)}`)
      const hdr = await headerText(page)
      check('(6) older same-revision result is NOT restored as current: marked NOT CURRENT, value dimmed, header has no current result',
        /^NOT CURRENT$/.test(await currentness(page)) && await page.locator('.result-section .metric.metric-stale').count() === 1 && /NO CURRENT RESULT/.test(hdr) && /no longer selects this run/.test(text),
        `older run ${short(jobB.run_id)} (value ${await page.getByTestId('metric-value').innerText()}) labelled "${await currentness(page)}"; header "${hdr}"`)
      const history = await page.locator('body').innerText()
      check('(6) nothing on the studio screen still claims CURRENT for the evaluation slot', !/CURRENT RUN\n/.test(history) || /NOT CURRENT/.test(history), 'provenance strip and run history inspected')
      const overflow = await shots(page, '04-cancelled-same-revision')
      check('(2)/(6) narrow 390 px layout has no horizontal page overflow in this state', overflow <= 1, `scrollWidth - innerWidth = ${overflow}px`)

      // Review pack must not present the unselected run as current either.
      const nav = page.getByRole('navigation', { name: 'Main navigation' })
      await nav.getByRole('button', { name: /Review/ }).click()
      await page.waitForTimeout(500)
      const report = await page.getByTestId('report-currentness').innerText().catch(() => '(no result block in review pack)')
      check('(6) review pack does not present the unselected run as current', !/^CURRENT\b/.test(report.trim()), report.replace(/\s+/g, ' ').slice(0, 120))
      await shots(page, '05-cancelled-review-pack')
      await nav.getByRole('button', { name: /Studio/ }).click()
      await page.waitForTimeout(300)
    }
    await drainFlood(flood)

    // Reload: the initial load must not resurrect the old run from the selection either.
    if (reached) {
      await page.reload()
      await page.getByText('Local backend connected').waitFor({ timeout: 20000 })
      await page.waitForTimeout(800)
      const hdr = await headerText(page)
      const section = await resultText(page).catch(() => '')
      check('(6) after a full reload the cancelled selection still yields no current evaluation result', /NO RESULT YET|NO CURRENT RESULT/.test(hdr) && !/(^|\n)CURRENT\n/.test(section) && await page.getByTestId('metric-value').count() === 0, `header "${hdr}"; result card "${section.replace(/\s+/g, ' ').slice(0, 50)}"`)
      await shots(page, '06-cancelled-after-reload')
    }

    // ---- (5)/(6) requirement edit -> new accepted revision -> its job is cancelled ---------------
    await runToEnd(page, page.getByRole('button', { name: /Evaluate planting/ }))
    sel = await selections(h0)
    const jobD = sel.evaluation.current_job
    check('recovery: a later evaluation on the same revision completes and is CURRENT again', jobD && jobD.status === 'completed' && /^CURRENT$/.test(await currentness(page)), jobD ? `job ${short(jobD.job_id)} run ${short(jobD.run_id)}` : 'no current job')

    prepared = await prepareFlood(h0, 1000)
    await page.getByRole('button', { name: 'Edit scenario' }).click()
    const budget = page.getByLabel('Upfront budget in pounds')
    const newBudgetPence = h0.input.constraints.budget_pence + 5000
    await budget.fill(String(newBudgetPence / 100))
    await budget.press('Enter')
    await page.waitForTimeout(300)
    check('(5) requirement edit is a draft: result marked stale against the draft before anything is accepted', /STALE · UNSAVED EDITS/.test(await currentness(page)) && (await head()).revision === h0.revision,
      `draft budget ${newBudgetPence} pence; backend head still rev ${h0.revision} with budget ${h0.input.constraints.budget_pence}`)
    await shots(page, '07-requirement-draft')
    await page.getByRole('button', { name: /Close editor|Close scenario editor/ }).first().click()
    flood = await submitFlood(prepared)
    await runAndCancel(page, page.getByRole('button', { name: /Accept changes/ }))
    const h1 = await head()
    const sel1 = await selections(h1)
    const newId = sel1.evaluation.selection?.accepted_job_id
    const jobE = newId ? await backend('GET', `/jobs/${newId}`) : null
    check('(5) accepted requirement edit is stored as the next revision with the edited value', h1.revision === h0.revision + 1 && h1.input.constraints.budget_pence === newBudgetPence,
      `backend head rev ${h1.revision}, budget_pence ${h1.input.constraints.budget_pence}, excluded_region_ids ${JSON.stringify(h1.input.constraints.excluded_region_ids)}`)
    if (!jobE || jobE.status !== 'cancelled') {
      notReachable('(6) newer-revision selection that does not complete', `the job for rev ${h1.revision} finished as "${jobE?.status}" before the Cancel click landed (raise CANOPY_FLOOD)`)
    } else {
      text = await resultText(page).catch(() => '')
      const hdr = await headerText(page)
      const label = text ? await currentness(page).catch(() => '') : '(no result shown)'
      check('(6) newer revision whose job was cancelled: backend has no current job for it', sel1.evaluation.current_job === null && jobE.scenario_revision === h1.revision && jobE.run_id === null,
        `job ${short(jobE.job_id)} status=${jobE.status} rev ${jobE.scenario_revision} error=${jobE.error?.code}`)
      check('(6) the older revision\'s result is NOT restored as current after the newer selection was cancelled',
        !/^CURRENT$/.test(label) && !/RESULT CURRENT/.test(hdr) && /Cancelled/.test(await jobLabel(page)) && (!text || /SUPERSEDED|NOT CURRENT/.test(label)),
        `rev ${h0.revision} run ${short(jobD.run_id)} labelled "${label}"; header "${hdr}"`)
      const overflow = await shots(page, '08-cancelled-new-revision')
      check('(6) narrow 390 px layout has no horizontal page overflow in this state', overflow <= 1, `scrollWidth - innerWidth = ${overflow}px`)
    }
    await drainFlood(flood)

    notReachable('(6) newer selection ending in status "failed" (rather than "cancelled")', 'this runtime gives no input a human can enter that makes a registered job fail: invalid edits are refused before a job exists (422 / REVISION_CONFLICT) and DEADLINE_EXCEEDED needs the scenario deadline (about one hour) to pass. The UI treats failed and cancelled through the same path (Selection.current_job is null, classifyResult -> not-selected). Covered by unit tests: evaluation.test.ts (classifyResult, describeJob failed/cancelled), shell.test.ts (headerStatus / provenanceStatus not-selected), useWorkspace.test.tsx; backend/tests/jobs/test_jobs.py.')
    check('no page errors', errors.length === 0, errors.join('; '))
  } catch (e) {
    check('script completed', false, String(e && e.stack ? e.stack : e).slice(0, 600))
    await page.screenshot({ path: join(evidenceDir, 'zz-failure.png'), fullPage: true }).catch(() => {})
  } finally {
    await browser.close()
  }
  const count = s => log.filter(l => l.status === s).length
  console.log(`\n${count('PASS')} PASS, ${count('FAIL')} FAIL, ${count('NOT-REACHABLE')} NOT-REACHABLE`)
  writeFileSync(join(evidenceDir, 'workspace-acceptance.json'), JSON.stringify({ url, api, session_started_at_utc: session?.started_at_utc ?? null, scenario_ref: session?.scenario_ref ?? null, viewports: [DESKTOP, NARROW], checks: log }, null, 2))
})()
