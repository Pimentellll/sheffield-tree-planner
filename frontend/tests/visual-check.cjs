const { chromium } = require('playwright-core')
const { createHash } = require('node:crypto')
const { mkdirSync } = require('node:fs')
const { join } = require('node:path')

const browserPath = process.env.CANOPY_BROWSER || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const url = process.env.CANOPY_URL || 'http://127.0.0.1:5173/'
const evidenceDir = join(__dirname, '..', 'artifacts')
const hash = bytes => createHash('sha256').update(bytes).digest('hex')
mkdirSync(evidenceDir, { recursive: true })

async function check(width, height) {
  const browser = await chromium.launch({ executablePath: browserPath, headless: true, args: ['--no-sandbox', '--disable-gpu'] })
  try {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 })
    const errors = []
    page.on('pageerror', error => errors.push(error.message))
    await page.goto(url)
    await page.getByText('SYNTHETIC TEST SITE', { exact: true }).waitFor()
    await page.waitForTimeout(300)
    const geometry = await page.evaluate(() => ({ viewport: innerWidth, scroll: document.documentElement.scrollWidth }))
    const sceneError = await page.getByRole('alert').count()
    const canvas = page.locator('.scene-canvas canvas')
    const before = hash(await canvas.screenshot())
    const orbit = page.getByRole('button', { name: 'Orbit camera left' })
    await orbit.focus()
    await page.keyboard.press('Enter')
    await page.waitForTimeout(350)
    const cameraChanged = before !== hash(await canvas.screenshot())
    await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: /city overview/i }).click()
    const overview = await page.getByRole('heading', { name: /Sheffield city overview/i }).count()
    await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: /planning studio/i }).click()
    const unavailable = await page.getByText('Backend not connected').count()
    const evaluateDisabled = await page.getByRole('button', { name: /Evaluate planting/i }).isDisabled()
    const screenshot = join(evidenceDir, `studio-${width}.png`)
    await page.screenshot({ path: screenshot })
    const result = { width, geometry, sceneError, cameraChanged, overview, unavailable, evaluateDisabled, errors, screenshot }
    console.log(JSON.stringify(result))
    if (geometry.scroll > geometry.viewport || sceneError || !cameraChanged || !overview || !unavailable || !evaluateDisabled || errors.length) process.exitCode = 1
  } finally { await browser.close() }
}

;(async () => {
  await check(1440, 900)
  await check(390, 844)
})().catch(error => { console.error(error); process.exitCode = 1 })
