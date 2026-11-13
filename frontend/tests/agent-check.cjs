// Planning-agent panel check in a real browser against a running CANOPY server.
// CANOPY_AGENT_EXPECT selects what the server was started with:
//   none        - no LLM_* configured: panel says so, start disabled, manual evaluation still works
//   unreachable - LLM_BASE_URL points at a closed loopback port: panel says unreachable, start disabled
//   live        - a real local model: run a goal, compare every shown ID/number with the backend
// Values are never hard-coded; nothing here is model output presented as evidence.
const { chromium } = require('playwright-core')
const { mkdirSync, writeFileSync, existsSync } = require('node:fs')
const { join } = require('node:path')

const browserPath = process.env.CANOPY_BROWSER || ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(existsSync)
const url = process.env.CANOPY_URL || 'http://127.0.0.1:8765/'
const api = (process.env.CANOPY_API || 'http://127.0.0.1:8765').replace(/\/$/, '')
const expectMode = process.env.CANOPY_AGENT_EXPECT || 'none'
const goal = process.env.CANOPY_AGENT_GOAL || 'Evaluate the current proposal and explain the computed additional shade.'
const evidenceDir = join(__dirname, '..', 'artifacts', `agent-${expectMode}`)
mkdirSync(evidenceDir, { recursive: true })
const log = []
const check = (name, ok, detail = '') => { log.push({ name, ok: Boolean(ok), detail }); if (!ok) process.exitCode = 1; console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`) }
const get = async path => { const r = await fetch(api + '/api/v1' + path); return { status: r.status, body: await r.json() } }
const short = (v, n = 12) => (v.length > n + 1 ? `${v.slice(0, n)}…` : v)

;(async () => {
  const browser = await chromium.launch({ executablePath: browserPath, headless: true, args: ['--no-sandbox', '--no-proxy-server'] })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } })
  const errors = []
  const requests = []
  page.on('pageerror', e => errors.push(e.message))
  page.on('request', r => requests.push(r.url()))
  let receipt = {}
  try {
    await page.goto(url)
    await page.getByText('Local backend connected').waitFor({ timeout: 20000 })
    const panel = page.getByTestId('agent')
    await panel.waitFor({ timeout: 10000 })
    const status = (await get('/agent/status')).body
    const availability = page.getByTestId('agent-availability')
    await page.waitForFunction(() => !/Checking/.test(document.querySelector('[data-testid=agent-availability]')?.textContent ?? 'Checking'), null, { timeout: 15000 })
    const shown = await availability.innerText()
    const ask = panel.getByRole('button', { name: /Ask the agent/ })
    check('panel never offers acceptance', await panel.getByRole('button', { name: /Accept/ }).count() === 0)

    if (expectMode === 'none') {
      check('server reports no model configured', status.configured === false)
      check('panel says not configured and start is disabled', /not configured/i.test(shown) && await ask.isDisabled(), shown.replace(/\s+/g, ' '))
      await page.getByRole('button', { name: /Evaluate planting/ }).click()
      await page.waitForFunction(() => /Completed/.test(document.querySelector('.job-status strong')?.textContent ?? ''), null, { timeout: 60000 })
      check('manual evaluation still completes without any model', /\d/.test(await page.getByTestId('metric-value').innerText()))
    } else if (expectMode === 'unreachable') {
      check('server reports model unreachable', status.configured === true && status.reachable === false, status.reason)
      check('panel says unreachable and start is disabled', /unreachable/i.test(shown) && await ask.isDisabled(), shown.replace(/\s+/g, ' '))
    } else {
      check('server reports a listed, reachable model', status.configured && status.reachable && status.model_listed, status.model)
      await panel.getByLabel('Goal for the planning agent').fill(goal)
      if (process.env.CANOPY_AGENT_SCOPE === 'evaluate') await panel.getByLabel('TOOLS').selectOption('evaluate')
      const started = page.waitForResponse(r => r.url().endsWith('/api/v1/agent/runs') && r.request().method() === 'POST')
      await ask.click()
      const runId = (await (await started).json()).run_id
      await page.waitForFunction(() => !/investigating|Stopping/.test(document.querySelector('[data-testid=agent-run-status] strong')?.textContent ?? 'investigating'), null, { timeout: 600000 })
      await page.waitForTimeout(300)
      const server = (await get(`/agent/runs/${runId}`)).body
      receipt = { run: server }
      const statusText = await page.getByTestId('agent-run-status').innerText()
      check('page shows the server run identity, model and turn count', statusText.includes(`Run ${short(runId, 8)}`) && statusText.includes(server.model) && statusText.includes(`${server.model_completions} model turn`), `${server.status}: ${server.reason ?? 'ok'}`)
      const toolRows = await page.locator('[data-testid=agent-tools] tbody tr').count()
      check('one tool row per server-recorded tool call', toolRows === server.tool_calls.length, `${toolRows} rows; ${server.tool_calls.map(c => `${c.operation}:${c.executed ? c.job_status : 'not executed'}`).join(', ')}`)
      for (const id of server.computed_run_ids) {
        const stored = await get(`/results/${id}`)
        check(`computed run ${short(id)} is a stored live backend Result for this task`, stored.status === 200 && stored.body.provenance.execution_mode === 'live' && stored.body.input_snapshot_ref.scenario_id === server.scenario_ref.scenario_id, stored.body.operation)
      }
      if (server.status === 'completed') {
        const evText = await page.getByTestId('agent-evidence').innerText()
        check('completed: every server-cited run is shown and verified', server.evidence_verified === true && server.cited_run_ids.every(id => evText.includes(short(id))), evText.replace(/\s+/g, ' '))
        const model = page.getByTestId('agent-model-text')
        check('model prose is separately labelled untrusted and equals the server field', await model.count() === 1 && /UNTRUSTED MODEL TEXT/.test(await model.innerText()) && (await model.innerText()).includes(server.untrusted_model_narrative.slice(0, 40)))
        await page.getByTestId('agent-summary').locator('summary').click()
        const summary = await page.getByTestId('agent-summary').locator('ul').innerText()
        check('summary on screen is the backend-generated summary', server.authoritative_summary.split('\n').every(line => summary.includes(line)))
        const stored = (await get(`/results/${server.cited_run_ids[0]}`)).body
        const shade = stored.metrics.find(m => m.metric_id === 'additional_shade')
        check('summary metric equals the stored Result', Boolean(shade) && summary.includes(`${shade.value} ${shade.unit}`), shade ? `${shade.value} ${shade.unit}` : 'none')
        // Bring the agent's runs into the studio: it must show the backend-selected current evaluation.
        await page.getByRole('button', { name: 'Show agent results in the studio' }).click()
        await page.getByText('Local backend connected').waitFor({ timeout: 20000 })
        await page.getByTestId('metric-value').waitFor({ timeout: 20000 })
        const ref = server.scenario_ref
        const scenario = (await get(`/scenarios/${ref.scenario_id}?revision=${ref.revision}`)).body
        const selections = (await get(`/scenarios/${ref.scenario_id}/selections?revision=${ref.revision}&scope=accepted`)).body
        const current = (await get(`/results/${selections.evaluation.current_job.run_id}`)).body
        const primary = current.metrics.find(m => m.metric_id === 'additional_shade' && m.case_id === scenario.input.objective.primary_case_id)
        const shown = await page.getByTestId('metric-value').innerText()
        check('studio shows the backend-selected current evaluation as CURRENT', shown === String(Number(primary.value.toFixed(6))) && /CURRENT\b/.test(await page.locator('.currentness strong').first().innerText()), `${shown} (run ${short(current.run_id)})`)
      } else {
        const st = await page.getByTestId('agent-run-status').innerText()
        check('non-completed run is shown as a safe failure without evidence', /failed safely|No validated|Stopped|budget/i.test(st) && await page.getByTestId('agent-evidence').count() === 0, st.replace(/\s+/g, ' '))
        if (server.computed_run_ids.length) {
          const uncited = await page.getByTestId('agent-uncited').innerText()
          check('computed-but-uncited runs are listed, not presented as evidence', server.computed_run_ids.every(id => uncited.includes(short(id))))
        }
      }
      await page.screenshot({ path: join(evidenceDir, 'agent-run.png'), fullPage: true })
    }
    check('browser never contacted a model endpoint', requests.every(u => u.startsWith(new URL(url).origin) || u.startsWith('data:')), `${requests.length} requests`)
    check('no page errors', errors.length === 0, errors.join('; '))
    await page.screenshot({ path: join(evidenceDir, 'agent-final.png'), fullPage: true })
  } catch (e) {
    check('script completed', false, String(e).slice(0, 300))
  } finally {
    await browser.close()
  }
  writeFileSync(join(evidenceDir, 'agent-check.json'), JSON.stringify({ url, api, expectMode, receipt, checks: log }, null, 2))
})()
