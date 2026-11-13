/* Real browser/API/numerical proof. No response body or metric is fabricated. */
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const net = require('node:net')
const { spawn } = require('node:child_process')
const { chromium } = require('playwright-core')

const root = path.resolve(__dirname, '../..')
const frontend = path.resolve(__dirname, '..')
const evidence = path.resolve(process.env.CANOPY_M2_EVIDENCE || path.join(frontend, 'artifacts', `m2-${Date.now()}`))
const python = process.env.CANOPY_PYTHON || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const installedOnly = process.env.CANOPY_M2_INSTALLED_ONLY === '1'
const numerical = process.env.CANOPY_NUMERICS_SOURCE
const browserPath = process.env.CANOPY_BROWSER || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
assert(numerical, 'CANOPY_NUMERICS_SOURCE must identify the pinned numerical checkout')
fs.mkdirSync(path.dirname(evidence), { recursive: true })
fs.mkdirSync(evidence)
const servedBuild = path.join(evidence, 'served-build')
fs.cpSync(path.join(frontend, 'dist'), servedBuild, { recursive: true })
const workspace = path.join(evidence, 'runtime')
const statusFile = path.join(evidence, 'server-status.json')
const cleanupFile = path.join(evidence, 'server-cleanup.json')
const out = fs.openSync(path.join(evidence, 'server.stdout.log'), 'w')
const err = fs.openSync(path.join(evidence, 'server.stderr.log'), 'w')
const server = spawn(python, [...(installedOnly ? ['-I'] : []), '-m', 'tree_planner.evaluators.ui_demo', '--workspace', workspace,
  '--numerical-source', numerical, '--frontend-dist', servedBuild, '--status-file', statusFile,
  '--cleanup-file', cleanupFile, '--control-stdin'], {
  cwd: root, windowsHide: true,
  env: { ...process.env, PYTHONPATH: installedOnly ? '' : path.join(root, 'backend', 'src') },
  stdio: ['pipe', out, err],
})
fs.closeSync(out); fs.closeSync(err)
server.stdin.on('error', () => {})
let serverExit = null
const exited = new Promise(resolve => server.once('exit', (code, signal) => {
  serverExit = { code, signal }; resolve(serverExit)
}))
const http = [], pageErrors = [], blocked = [], pending = new Set()
const receipt = { scope: 'Real synthetic one-tree browser → API → job → pinned numerical calculation; no full planner or real-site acceptance', pythonMode: installedOnly ? 'isolated installed wheel' : 'explicit source checkout', evidence, serverPid: server.pid, phases: [] }
let browser, page, base, failure, releaseHeld
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))
async function until(predicate, label, timeout = 25000) {
  const deadline = Date.now() + timeout
  while (Date.now() < deadline) {
    if (await predicate()) return
    if (serverExit) throw new Error(`Owned server exited during ${label}: ${JSON.stringify(serverExit)}`)
    await sleep(60)
  }
  throw new Error(`Timed out: ${label}`)
}
async function api(route) {
  const response = await fetch(base + route)
  if (!response.ok) throw new Error(`${route}: ${response.status} ${await response.text()}`)
  return response.json()
}
async function runText() {
  const loc = page.getByTestId('run-id')
  if (!await loc.count()) return ''
  const text = (await loc.innerText()).trim()
  return text.startsWith('Run: ') ? text.slice('Run: '.length).trim() : text
}
async function metricText() {
  const loc = page.getByTestId('current-metric')
  return await loc.count() ? (await loc.innerText()).trim() : ''
}
async function checkResult(expected) {
  await until(async () => /^[a-f0-9]{32}$/.test(await runText()), 'actual run identity rendered')
  const run = await runText(), result = await api('/api/v1/results/' + run)
  const metrics = result.metrics.filter(m => m.metric_id === 'additional_shade' && m.unit === 'm2_h')
  assert.equal(metrics.length, 1)
  assert.equal(metrics[0].value, expected)
  assert.equal(Number.parseFloat(await metricText()), metrics[0].value)
  const session = await api('/m2/session'), ref = session.scenario
  const slots = await api(`/api/v1/scenarios/${encodeURIComponent(ref.scenario_id)}/selections?revision=${ref.revision}&scope=accepted`)
  assert.equal(slots.evaluation.current_job.run_id, run)
  assert.equal(result.input_snapshot_ref.revision, ref.revision)
  assert.equal(result.input_snapshot_ref.scenario_id, ref.scenario_id)
  assert.equal(slots.evaluation.current_job.input_fingerprint, result.input_fingerprint)
  receipt.phases.push({ run_id: run, source_job_id: result.source_job_id, scenario_ref: result.input_snapshot_ref,
    input_fingerprint: result.input_fingerprint, metric: metrics[0], source_hashes: result.provenance.source_hashes })
  return { run, result, session }
}
async function placement(name, east) {
  const before = await api('/m2/session')
  await page.getByRole('button', { name, exact: true }).click()
  await until(async () => {
    const now = await api('/m2/session')
    return now.scenario.revision > before.scenario.revision && now.layout.placements[0].position_enu_m[0] === east
  }, 'human scenario revision accepted')
  await until(async () => !/^[a-f0-9]{32}$/.test(await runText()), 'previous result invalidated')
  await until(() => page.getByRole('button', { name: /Evaluate planting/i }).isEnabled(), 'evaluate enabled for accepted revision')
}
async function evaluate(expected) {
  await page.getByRole('button', { name: /Evaluate planting/i }).click()
  return checkResult(expected)
}

;(async () => {
  try {
    await until(async () => {
      if (!fs.existsSync(statusFile)) return false
      try {
        base = JSON.parse(fs.readFileSync(statusFile, 'utf8')).url
        assert.equal(new URL(base).hostname, '127.0.0.1')
        return (await fetch(base + '/api/v1/health')).ok
      } catch { return false }
    }, 'owned loopback API ready')
    browser = await chromium.launch({ executablePath: browserPath, headless: true, args: ['--disable-gpu'] })
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, serviceWorkers: 'block' })
    await context.route('**/*', route => {
      const url = route.request().url()
      if (new URL(url).origin !== base) {
        blocked.push(url); return route.abort('blockedbyclient')
      }
      return route.continue()
    })
    page = await context.newPage()
    page.on('pageerror', e => pageErrors.push(e.message))
    page.on('response', response => {
      const url = response.url()
      if (!url.startsWith(base + '/api/') && !url.startsWith(base + '/m2/')) return
      const record = { url, method: response.request().method(), status: response.status() }
      http.push(record)
      const task = response.json().then(body => { record.body = body }).catch(e => { record.read_error = `${e.name}: ${e.message}` })
      pending.add(task); task.finally(() => pending.delete(task))
    })
    await page.goto(base, { waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {
      receipt.networkidle = 'Periodic currentness polling; DOM readiness checked explicitly'
    })
    await until(() => page.getByRole('button', { name: /Evaluate planting/i }).isEnabled(), 'real evaluation UI connected')
    assert((await page.locator('body').innerText()).toLowerCase().includes('synthetic'))
    const positive = await evaluate(2.0)
    await page.screenshot({ path: path.join(evidence, 'positive-desktop.png'), fullPage: true })
    await placement('Missed-tree placement', 3)
    const zero = await evaluate(0.0)
    assert.notEqual(zero.run, positive.run)
    await page.screenshot({ path: path.join(evidence, 'zero-desktop.png'), fullPage: true })

    // Hold a genuine old result response, never synthesize or alter its payload.
    await placement('Reference placement', 0)
    let heldResult, sawHeld, finishedHeld
    const heldSeen = new Promise(resolve => { sawHeld = resolve })
    const heldResponseFinished = new Promise(resolve => { finishedHeld = resolve })
    const gate = new Promise(release => { releaseHeld = release })
    await page.route('**/api/v1/results/*', async route => {
      const response = await route.fetch()
      heldResult = await response.json()
      sawHeld()
      await gate
      try { await route.fulfill({ response }) } catch (e) { receipt.old_response_abort = e.name }
      finishedHeld()
    }, { times: 1 })
    await page.getByRole('button', { name: /Evaluate planting/i }).click()
    await Promise.race([heldSeen, sleep(20000).then(() => { throw new Error('No actual old result request to delay') })])
    assert.equal(heldResult.metrics.find(m => m.metric_id === 'additional_shade').value, 2.0)
    await placement('Missed-tree placement', 3)
    await page.evaluate(() => {
      window.__m2Paints = []
      new MutationObserver(() => {
        window.__m2Paints.push({ run: document.querySelector('[data-testid="run-id"]')?.textContent || '',
          metric: document.querySelector('[data-testid="current-metric"]')?.textContent || '' })
      }).observe(document.body, { childList: true, subtree: true, characterData: true })
    })
    const current = await evaluate(0.0)
    releaseHeld(); releaseHeld = null
    await heldResponseFinished
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
    const paints = await page.evaluate(() => window.__m2Paints)
    assert(!paints.some(p => p.run.includes(heldResult.run_id)), 'Old completion appeared as current')
    assert.equal(await runText(), current.run)
    receipt.stale = { held_actual_run: heldResult.run_id, current_run: current.run, no_old_paint: true, paints }
    await page.screenshot({ path: path.join(evidence, 'stale-suppressed.png'), fullPage: true })

    const asset = path.join(workspace, 'inputs', 'synthetic-reference.json')
    const original = fs.readFileSync(asset)
    try {
      fs.writeFileSync(asset, 'controlled changed source bytes')
      await until(async () => await page.getByRole('alert').count() > 0 && !/^[a-f0-9]{32}$/.test(await runText()), 'real source failure clears displayed result')
      assert(!Number.isFinite(Number.parseFloat(await metricText())))
      await until(() => http.some(r => r.status === 409), 'browser observes actual source-conflict status')
      // The UI deliberately throws on non-OK status without consuming its body.
      // Probe that same live endpoint independently rather than invent a CDP body.
      const rejected = await fetch(base + '/m2/session')
      const rejectedBody = await rejected.json()
      assert.equal(rejected.status, 409)
      assert.equal(rejectedBody.code, 'REVISION_CONFLICT')
      receipt.source_failure_probe = { transport: 'actual independent loopback fetch',
        path: '/m2/session', status: rejected.status, body: rejectedBody }
      await page.screenshot({ path: path.join(evidence, 'source-failure.png'), fullPage: true })
    } finally { fs.writeFileSync(asset, original) }
    await until(() => page.getByRole('button', { name: /Evaluate planting/i }).isEnabled(), 'source restoration re-admitted')
    const recovery = await evaluate(0.0)
    assert.notEqual(recovery.run, current.run)
    receipt.failure_recovery = { actual_source_gate: true, old_metric_hidden: true, restored_run: recovery.run }

    await page.setViewportSize({ width: 390, height: 844 })
    await placement('Reference placement', 0)
    await evaluate(2.0)
    const layout = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }))
    assert(layout.scroll <= layout.width, `Horizontal overflow: ${JSON.stringify(layout)}`)
    receipt.mobile = layout
    await page.screenshot({ path: path.join(evidence, 'positive-mobile.png'), fullPage: true })
    assert.equal(pageErrors.length, 0, JSON.stringify(pageErrors))
    assert.equal(blocked.length, 0, JSON.stringify(blocked))
    receipt.status = 'passed'
  } catch (error) {
    failure = error
    receipt.status = 'failed'; receipt.error = error.stack
    if (page) await page.screenshot({ path: path.join(evidence, 'failure-state.png'), fullPage: true }).catch(() => {})
  } finally {
    if (releaseHeld) releaseHeld()
    if (browser) await browser.close()
    await Promise.allSettled([...pending])
    if (!serverExit) { server.stdin.write('{"action":"shutdown"}\n'); server.stdin.end() }
    const stopped = await Promise.race([exited.then(() => true), sleep(12000).then(() => false)])
    if (!stopped) {
      receipt.forced_cleanup = true
      spawn('taskkill.exe', ['/PID', String(server.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' })
      await exited
    }
    receipt.server_exit = serverExit
    receipt.cleanup = fs.existsSync(cleanupFile) ? JSON.parse(fs.readFileSync(cleanupFile, 'utf8')) : null
    if (base) {
      const port = Number(new URL(base).port)
      receipt.port_closed = await new Promise(resolve => {
        const sock = net.connect({ host: '127.0.0.1', port })
        sock.once('connect', () => { sock.destroy(); resolve(false) })
        sock.once('error', () => resolve(true))
      })
    }
    receipt.page_errors = pageErrors; receipt.blocked_external = blocked
    fs.writeFileSync(path.join(evidence, 'http-trace.json'), JSON.stringify(http, null, 2))
    fs.writeFileSync(path.join(evidence, 'verification.json'), JSON.stringify(receipt, null, 2))
    console.log(JSON.stringify({ status: receipt.status, evidence, phases: receipt.phases.length,
      cleanup: receipt.cleanup, port_closed: receipt.port_closed, error: failure?.message }))
    if (failure || receipt.forced_cleanup || serverExit?.code !== 0 || !receipt.port_closed ||
      !receipt.cleanup?.owned_listener_closed || !receipt.cleanup?.owned_worker_stopped) process.exitCode = 1
  }
})().catch(e => { console.error(e); process.exitCode = 1 })
