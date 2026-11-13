// UI check for the view-only terrain context. Run the dev server with CANOPY_TERRAIN_DIR pointing at
// scripts/make_test_terrain.py output (labelled synthetic), or unset to check the "not loaded" state.
// No backend is needed. CANOPY_TERRAIN_EXPECT=absent|synthetic|real selects the expectations.
const { chromium } = require('playwright-core')
const { createHash } = require('node:crypto')
const { mkdirSync, writeFileSync, existsSync } = require('node:fs')
const { join } = require('node:path')
const browserPath = process.env.CANOPY_BROWSER || (process.platform === 'win32' ? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe' : ['/usr/bin/google-chrome', '/usr/bin/chromium'].find(existsSync))
const url = process.env.CANOPY_URL || 'http://127.0.0.1:5173/'
const expect = process.env.CANOPY_TERRAIN_EXPECT || 'synthetic'
const dir = join(__dirname, '..', 'artifacts', 'terrain'); mkdirSync(dir, { recursive: true })
const log = []
const check = (name, ok, detail = '') => { log.push({ name, ok: Boolean(ok), detail }); if (!ok) process.exitCode = 1; console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`) }
const hash = b => createHash('sha256').update(b).digest('hex')
;(async () => {
  const browser = await chromium.launch({ executablePath: browserPath, headless: true, args: ['--no-sandbox', '--no-proxy-server'] })
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } })
  const errors = []; page.on('pageerror', e => errors.push(e.message))
  try {
    await page.goto(url)
    await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: /Sheffield sites/ }).click()
    if (expect === 'absent') {
      await page.getByTestId('terrain-absent').waitFor({ timeout: 15000 })
      check('without a terrain file the view says "Not loaded" and draws nothing', await page.locator('.terrain-panel canvas').count() === 0)
    } else {
      await page.getByTestId('terrain-view').waitFor({ timeout: 30000 })
      await page.waitForTimeout(1200)
      const tag = await page.getByTestId('terrain-tag').innerText()
      check(expect === 'synthetic' ? 'synthetic terrain is labelled synthetic, not Sheffield' : 'real terrain is labelled view only, not analysed', expect === 'synthetic' ? /SYNTHETIC · NOT SHEFFIELD/.test(tag) : /VIEW ONLY · NOT ANALYSED/.test(tag), tag)
      const notes = await page.locator('.terrain-notes').innerText()
      check('notes say the surface is not loaded into the planner', /not loaded into the planner and no shade result refers to it/.test(notes))
      if (expect === 'real') check('attribution and licence are shown', /Environment Agency copyright/.test(notes) && /Open Government Licence/.test(notes))
      const canvas = page.locator('.terrain-panel canvas')
      const a = hash(await canvas.screenshot())
      await page.getByRole('button', { name: 'Orbit camera left' }).last().click(); await page.waitForTimeout(500)
      const b = hash(await canvas.screenshot())
      await page.getByRole('button', { name: 'From above' }).click(); await page.waitForTimeout(500)
      const c = hash(await canvas.screenshot())
      const box = await canvas.boundingBox()
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2); await page.mouse.wheel(0, -600); await page.waitForTimeout(500)
      const d = hash(await canvas.screenshot())
      check('terrain is navigable: orbit, top view and scroll zoom each change the view', new Set([a, b, c, d]).size === 4)
      await page.getByRole('button', { name: 'Reset view' }).last().click(); await page.waitForTimeout(600)
      await page.screenshot({ path: join(dir, `${expect}-1920.png`) })
      await page.locator('.terrain-panel').screenshot({ path: join(dir, `${expect}-panel.png`) })
    }
    check('no page errors', errors.length === 0, errors.join('; '))
  } catch (e) { check('script completed', false, String(e).slice(0, 300)) }
  await browser.close()
  writeFileSync(join(dir, `terrain-check-${expect}.json`), JSON.stringify({ url, expect, checks: log }, null, 2))
})()
