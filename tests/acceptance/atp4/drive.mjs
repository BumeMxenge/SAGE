// ATP-4's driver: plays each scenario in a real browser against the test's frontend on 3001, whose API
// is the test server on 8001, and writes what each run saw to the file it's given. For every screen
// that's the address, the rail's line naming the plan or pair, and the conversation's messages, then
// the API's own chats and her plan set, before and after. It loads the frontend's own Playwright by
// path, as frontend/e2e/ and playwright.config.ts belong to app foundations.
//   node drive.mjs <sign-in link> <output file> <planted: yes or no> <scenario>...
import { execFileSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'

const require = createRequire(new URL('../../../frontend/package.json', import.meta.url))
const { chromium } = require('@playwright/test')

const WEB = 'http://localhost:3001'
const API = 'http://localhost:8001'
const BACKEND = fileURLToPath(new URL('../../../backend/', import.meta.url))
const STUDENT = fileURLToPath(new URL('./student.py', import.meta.url))
// Ten runs a scenario. RUNS=1 tries the harness out, with the same first draws.
const RUNS = Number(process.env.RUNS ?? 10)
const SEED = 4022
// Time for a screen to take in a reply once it's saved, before the screen is read
const SETTLE = 1500

const [link, out, planted, ...scenarios] = process.argv.slice(2)

// mulberry32, a small seeded generator, so every run's delay and switch time can be drawn again
function generator(seed) {
  let state = seed >>> 0
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let mixed = Math.imul(state ^ (state >>> 15), state | 1)
    mixed ^= mixed + Math.imul(mixed ^ (mixed >>> 7), mixed | 61)
    return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296
  }
}

// Each scenario's ten runs: a delay of 0 to 8 s, a switch time inside it, and a second tab's delay.
// The planted fault's runs draw the same, numbered from 51, so their questions never match the
// scenarios' own, which her chats still hold.
function draws(scenario) {
  const next = generator(SEED + Number(scenario.slice(1)))
  const tenths = (value) => Math.round(value * 10) / 10
  const first = planted === 'yes' ? 51 : 1
  return Array.from({ length: RUNS }, (_, index) => {
    const delay = tenths(8 * next())
    const run = first + index
    return { id: `${scenario}-${String(run).padStart(2, '0')}`, run, delay, switchAt: tenths(delay * next()), second: tenths(8 * next()) }
  })
}

const sleep = (ms) => new Promise((done) => setTimeout(done, Math.max(ms, 0)))
const startingWith = (text) => new RegExp(`^${text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`)
const rail = (page) => page.getByRole('complementary', { name: 'Assistant' })
const isAsk = (request) => request.method() === 'POST' && /^\/v1\/chats\/[^/]+\/messages$/.test(new URL(request.url()).pathname)

// The API as the page's own session reads it
async function api(page, path) {
  return page.evaluate(
    async ([base, path]) => {
      const key = Object.keys(localStorage).find((name) => /^sb-.*-auth-token$/.test(name))
      const { access_token: token } = JSON.parse(localStorage.getItem(key))
      const response = await fetch(base + path, { headers: { Authorization: `Bearer ${token}` } })
      if (!response.ok) throw new Error(`${path} answered ${response.status}`)
      return response.json()
    },
    [API, path],
  )
}

async function planSet(page) {
  const set = await api(page, '/v1/plans')
  return set.plans.map(({ id, name, position, hidden }) => ({ id, name, position, hidden }))
}

// Her chats on a plan or pair, each with its messages
async function chatsOf(page, planId, otherPlanId = null) {
  const [first, second] = otherPlanId ? [planId, otherPlanId].sort() : [planId, null]
  const chats = await api(page, `/v1/chats?plan_id=${first}${second ? `&other_plan_id=${second}` : ''}`)
  return Promise.all(
    chats.map(async (chat) => ({
      id: chat.id,
      plan_id: chat.plan_id,
      other_plan_id: chat.other_plan_id,
      messages: (await api(page, `/v1/chats/${chat.id}/messages`)).map(({ role, content }) => ({ role, content })),
    })),
  )
}

async function openAssistant(page) {
  const open = page.getByRole('button', { name: 'Open Assistant', exact: true })
  const fresh = page.getByRole('button', { name: 'New Chat', exact: true })
  await open.or(fresh).first().waitFor()
  if (await open.isVisible()) await open.click()
  await fresh.waitFor()
}

// Waits until the rail names the plan or pair now in the address, as a person acts only on what the
// screen shows: during a switch the address moves first, and the old plan stays on screen until the
// new one is drawn. After 15 s it goes on regardless, so a rail that never catches up still counts.
async function showing(page, ...names) {
  const [first, second] = names.map((name) => name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const line = second ? `Comparing (${first} and ${second}|${second} and ${first})` : `Reading ${first}`
  await rail(page)
    .locator('header p')
    .filter({ hasText: new RegExp(`^${line}$`) })
    .first()
    .waitFor({ timeout: 15_000 })
    .catch(() => {})
}

async function load(page, plan) {
  await page.goto(`${WEB}/plan/${plan.id}`)
  await page.waitForURL(`**/plan/${plan.id}`)
  await openAssistant(page)
  await showing(page, plan.name)
}

// Asks in a new chat. Returns when the question has left, with when it left and a promise of when its
// reply came back, or null if the page went before it did.
async function ask(page, words) {
  await page.getByRole('button', { name: 'New Chat', exact: true }).click()
  await page.getByRole('textbox', { name: 'Ask SAGE' }).fill(words)
  const leaving = page.waitForRequest(isAsk)
  const back = page.waitForResponse((response) => isAsk(response.request()), { timeout: 60_000 }).then(
    () => Date.now(),
    () => null,
  )
  await page.getByRole('button', { name: 'Send', exact: true }).click()
  await leaving
  return { sent: Date.now(), back }
}

async function switchPlan(page, from, to) {
  await page.getByRole('button', { name: startingWith(from.name) }).first().click()
  await page.getByRole('option', { name: startingWith(to.name) }).click()
  await page.waitForURL(`**/plan/${to.id}`)
  await showing(page, to.name)
}

// What the screen shows, once the rail names its plan or pair and the conversation has arrived
async function screen(page, label) {
  const line = rail(page).locator('header p').filter({ hasText: /^(Reading|Comparing) / })
  await line.first().waitFor()
  const log = page.getByRole('log', { name: 'Conversation' })
  await log.or(page.getByText(/^I can (answer questions about|compare these two plans)/)).first().waitFor()
  const url = new URL(page.url())
  return {
    label,
    address: url.pathname + url.search,
    header: (await line.first().textContent()).trim(),
    messages: (await log.locator('p').allTextContents()).map((text) => text.trim()),
  }
}

// When the reply to a question appears in the API, polled, or null if it never does
async function saved(page, planId, question, deadline) {
  while (Date.now() < deadline) {
    const chats = await chatsOf(page, planId)
    if (chats.some((chat) => chat.messages.some((m) => m.role === 'assistant' && m.content.startsWith(`${question} answered`)))) {
      return Date.now()
    }
    await sleep(250)
  }
  return null
}

async function reloaded(page) {
  await page.reload()
  await openAssistant(page)
}

const asked = (question, planId, otherPlanId = null) => ({ question, plan_id: planId, other_plan_id: otherPlanId })

// Each scenario plays one run on fresh pages and returns what it saw
const play = {
  // Ask, then switch plan before the reply
  async S1(context, run, { shown: [a, b] }) {
    const page = await context.newPage()
    await load(page, a)
    const before = await planSet(page)
    const question = `${run.id}-1`
    const { sent, back } = await ask(page, `[${question}] [d=${run.delay}] Is this plan clash-free?`)
    await sleep(run.switchAt * 1000 - (Date.now() - sent))
    await switchPlan(page, a, b)
    const switched = Date.now()
    const replied = await back
    await sleep(SETTLE)
    const views = [await screen(page, 'the other plan, once the reply is saved')]
    await switchPlan(page, b, a)
    await sleep(SETTLE)
    views.push(await screen(page, 'the plan asked about, once the reply is saved'))
    await reloaded(page)
    views.push(await screen(page, 'the plan asked about, after a reload'))
    const chats = [...(await chatsOf(page, a.id)), ...(await chatsOf(page, b.id))]
    const after = await planSet(page)
    await page.close()
    return { switch_at: run.switchAt, race: replied === null || switched < replied, asked: [asked(question, a.id)], views, chats, plans_before: before, plans_after: after }
  },

  // Switch plan, then ask
  async S2(context, run, { shown: [a, b] }) {
    const page = await context.newPage()
    await load(page, a)
    const before = await planSet(page)
    await switchPlan(page, a, b)
    const question = `${run.id}-1`
    const { back } = await ask(page, `[${question}] [d=${run.delay}] How many credits is this plan?`)
    await back
    await sleep(SETTLE)
    const views = [await screen(page, 'the plan switched to, once the reply is saved')]
    await reloaded(page)
    views.push(await screen(page, 'the plan switched to, after a reload'))
    const chats = [...(await chatsOf(page, a.id)), ...(await chatsOf(page, b.id))]
    const after = await planSet(page)
    await page.close()
    return { race: false, asked: [asked(question, b.id)], views, chats, plans_before: before, plans_after: after }
  },

  // Compare two plans, then ask
  async S3(context, run, { shown: [a], names }) {
    const page = await context.newPage()
    await load(page, a)
    const before = await planSet(page)
    await page.getByRole('button', { name: 'Compare', exact: true }).click()
    await page.waitForURL(/\?compare=/)
    const other = new URL(page.url()).searchParams.get('compare')
    await showing(page, a.name, names[other])
    const question = `${run.id}-1`
    const { back } = await ask(page, `[${question}] [d=${run.delay}] How do these plans differ?`)
    await back
    await sleep(SETTLE)
    const views = [await screen(page, 'the pair, once the reply is saved')]
    await reloaded(page)
    views.push(await screen(page, 'the pair, after a reload'))
    const chats = [...(await chatsOf(page, a.id, other)), ...(await chatsOf(page, a.id)), ...(await chatsOf(page, other))]
    const after = await planSet(page)
    await page.close()
    return { race: false, asked: [asked(question, a.id, other)], views, chats, plans_before: before, plans_after: after }
  },

  // Reload while the reply is on its way. The browser drops the request, but the server finishes the
  // turn and saves it.
  async S4(context, run, { shown: [a] }) {
    const page = await context.newPage()
    await load(page, a)
    const before = await planSet(page)
    const question = `${run.id}-1`
    const { sent } = await ask(page, `[${question}] [d=${run.delay}] When is my first class?`)
    await sleep(run.switchAt * 1000 - (Date.now() - sent))
    await reloaded(page)
    const reload = Date.now()
    const stored = await saved(page, a.id, question, sent + run.delay * 1000 + 20_000)
    await sleep(SETTLE)
    const views = [await screen(page, 'after a reload mid-reply, once the reply is saved')]
    await reloaded(page)
    views.push(await screen(page, 'after another reload'))
    const chats = await chatsOf(page, a.id)
    const after = await planSet(page)
    await page.close()
    return { switch_at: run.switchAt, race: stored === null || reload < stored, asked: [asked(question, a.id)], views, chats, plans_before: before, plans_after: after }
  },

  // Two tabs ask on different plans at once
  async S5(context, run, { shown: [a, b] }) {
    const one = await context.newPage()
    const two = await context.newPage()
    await load(one, a)
    await load(two, b)
    const before = await planSet(one)
    const first = `${run.id}-1`
    const second = `${run.id}-2`
    const asking = await Promise.all([
      ask(one, `[${first}] [d=${run.delay}] Is this plan clash-free?`),
      ask(two, `[${second}] [d=${run.second}] Is this plan clash-free?`),
    ])
    const replies = await Promise.all(asking.map(({ back }) => back))
    await sleep(SETTLE)
    const views = [await screen(one, 'the first tab, once both replies are saved'), await screen(two, 'the second tab, once both replies are saved')]
    await reloaded(one)
    await reloaded(two)
    views.push(await screen(one, 'the first tab, after a reload'), await screen(two, 'the second tab, after a reload'))
    const chats = [...(await chatsOf(one, a.id)), ...(await chatsOf(one, b.id))]
    const after = await planSet(one)
    await one.close()
    await two.close()
    // Both turns in flight at once
    const race = replies.every((replied) => replied !== null) && asking[1].sent < replies[0] && asking[0].sent < replies[1]
    return { second_delay: run.second, race, asked: [asked(first, a.id), asked(second, b.id)], views, chats, plans_before: before, plans_after: after }
  },

  // Press Open Plan on a hidden plan a reply offers
  async S6(context, run, { shown: [a], hidden: [offered] }) {
    const page = await context.newPage()
    await load(page, a)
    const before = await planSet(page)
    const question = `${run.id}-1`
    const { back } = await ask(page, `[${question}] [d=${run.delay}] [offer] Is there a plan with another elective?`)
    await back
    await page.getByRole('link', { name: `Open ${offered.name}`, exact: true }).click()
    await page.waitForURL(`**/plan/${offered.id}`)
    await showing(page, offered.name)
    await sleep(SETTLE)
    const views = [await screen(page, 'the offered plan, after Open Plan')]
    await reloaded(page)
    views.push(await screen(page, 'the offered plan, after a reload'))
    const chats = [...(await chatsOf(page, a.id)), ...(await chatsOf(page, offered.id))]
    const after = await planSet(page)
    await page.close()
    // Hidden again, so the next run starts from her set as it was
    execFileSync(`${BACKEND}.venv/bin/python`, [STUDENT, 'hide'], { cwd: BACKEND, stdio: 'inherit' })
    return { race: false, offered: offered.id, asked: [asked(question, a.id)], views, chats, plans_before: before, plans_after: after }
  },
}

const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1280, height: 820 } })
const start = await context.newPage()
await start.goto(link)
await start.waitForURL(/\/plan\/[\w-]+$/)
const set = await planSet(start)
await start.close()
const byPosition = (one, other) => one.position - other.position
const names = Object.fromEntries(set.map((plan) => [plan.id, plan.name]))
const plans = { shown: set.filter((plan) => !plan.hidden).sort(byPosition), hidden: set.filter((plan) => plan.hidden).sort(byPosition), names }
const observations = []
for (const scenario of scenarios) {
  for (const run of draws(scenario)) {
    const seen = await play[scenario](context, run, plans)
    observations.push({ scenario, run: run.run, planted: planted === 'yes', delay: run.delay, switch_at: null, offered: null, plans: names, ...seen })
    console.log(`${run.id}${planted === 'yes' ? ' with the planted fault' : ''}: done`)
  }
}
writeFileSync(out, `${JSON.stringify(observations, null, 2)}\n`)
await browser.close()
