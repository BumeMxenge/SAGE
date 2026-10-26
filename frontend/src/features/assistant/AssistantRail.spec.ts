// The assistant as Mbali, beside her real plans, with every chat request answered by made-up data, so
// no check reaches the advisor, spends money or writes a chat into the database every worktree
// shares. A catch-all refuses any chat request a check leaves unanswered, and fails the check. It
// checks that the chat follows the address, for a plan and for a pair, and that a pair's first
// question makes its chat with both plans; that a reply shows its sources, the line to her student
// advisor and Open Plan, and a plan her answers hid that it offers joins her plan list at once and
// opens as one of hers; that advisor_unavailable keeps her
// question and Try Again sends the same words to the same chat; that nothing more goes while a reply
// is on its way, though a question in another plan or pair does; that the chat list is read again
// after a reply, so the advisor's title replaces New Chat; that a question cut off on its way is
// checked against the chat before Try Again is offered; that no assistant shows while her set still
// needs its questions answered; that Compare and the view toggle show only their icons while the
// sidebar and the assistant are both open; and that the toggles hand focus to each other. While its
// reads are held on their way, the folded strip shows at a plan's address until her set says it needs
// its questions answered, and open, the header renders at once over bubble-shaped skeletons, its plan
// or pair's name a skeleton too, with Send held, each passing axe and photographed beside what it turns
// into. After a reply, her set is read again with no skeleton, no blank switcher and no fade. Then axe
// and the keyboard walk in both themes, and parity beside the planner prototype, the loading sheet's
// case 03 and the error sheet's case 09.
import { expect, type Page, type Route, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../../e2e/axe.ts'
import { walkKeyboard } from '../../../e2e/keyboard.ts'
import {
  forgetSeen,
  hold,
  loading,
  photographArrival,
  read,
  seenLoading,
  settledArrival,
  skeletons,
  watchLoading,
} from '../../../e2e/loading.ts'
import { type ParityCase, parity, type Theme } from '../../../e2e/parity.ts'
import { settled } from '../../../e2e/settled.ts'
import { mbali } from '../../../e2e/visitors.ts'
import type { components } from '../../lib/api-types.ts'

test.use({ storageState: mbali })

type PlanSet = components['schemas']['PlanSet']
type Chat = components['schemas']['Chat']
type Message = components['schemas']['Message']
type Citation = components['schemas']['Citation']
type Problem = components['schemas']['Problem']

// The API is on another port, so each answer allows this page's origin, as the backend's CORS does
const allowed = { 'Access-Control-Allow-Origin': '*' }
const planAddress = /\/plan\/[\w-]+$/
const chatRequests = (url: URL) => url.pathname.startsWith('/v1/chats')

// No check may reach the advisor: a chat request no check answers is refused, and fails the check
let unanswered: string[] = []
test.beforeEach(async ({ page }) => {
  unanswered = []
  await page.route(chatRequests, (route) => {
    unanswered.push(`${route.request().method()} ${route.request().url()}`)
    return route.abort()
  })
})
test.afterEach(() => {
  expect(unanswered).toEqual([])
})

// Made-up ids for chats and messages, one after another
let made = 0
const madeUpId = () => `00000000-0000-4000-8000-${String((made += 1)).padStart(12, '0')}`

function messageOf(role: Message['role'], content: string, fields: Partial<Message> = {}): Message {
  return {
    id: madeUpId(),
    role,
    content,
    term: 'sem1',
    created_at: '2026-10-23T10:00:00Z',
    referral: false,
    open_plan_id: null,
    citations: [],
    ...fields,
  }
}

const chatOf = (planId: string, title: string | null = null): Chat => ({
  id: madeUpId(),
  plan_id: planId,
  other_plan_id: null,
  title,
  created_at: '2026-10-23T09:00:00Z',
})

const refusalOf = (code: Problem['code'], status: number): Problem => ({
  type: 'about:blank',
  title: 'Made Up',
  status,
  detail: 'A made-up refusal.',
  code,
})

// The prototype's answer to its suggested question, with what the API adds to a reply: two sources
// from the handbook, made-up quotes, and the line to her student advisor
const clashFree =
  'This plan is clash-free in every term. Wednesday afternoon stays open for the faculty practical block, and nothing overlaps the Monday project supervision.'
const handbook = 'UCT Faculty of Engineering & the Built Environment Undergraduate Handbook 2026 (Book 7a)'
const sources: Citation[] = [
  { position: 1, quote: 'A made-up rule on clashing meetings.', source: handbook, section: 'Made-up Rules', page: 31 },
  { position: 2, quote: 'A made-up row of a curriculum table.', source: handbook, section: 'Made-up Curriculum', page: 58 },
]

type Question = { chatId: string; content: string; term: string }

// How the made-up advisor answers a question: with a reply, saved with the question, and perhaps the
// chat's first title; with a refusal, which saves nothing; or with a dropped connection, after the
// exchange was saved or before
type Answer = { reply: Message; title?: string } | { refusal: Problem } | { drop: 'saved' | 'lost' }

type MadeUpChats = {
  chats?: Chat[]
  messages?: Record<string, Message[]>
  answer?: (question: Question) => Answer | Promise<Answer>
}

const refuse = (route: Route, problem: Problem) =>
  route.fulfill({ status: problem.status, contentType: 'application/problem+json', json: problem, headers: allowed })

// A chat on exactly this plan, or this pair in either order, as the API matches them
const holds = (chat: Chat, planId: string | null, otherPlanId: string | null) =>
  otherPlanId === null
    ? chat.plan_id === planId && chat.other_plan_id === null
    : (chat.plan_id === planId && chat.other_plan_id === otherPlanId) ||
      (chat.plan_id === otherPlanId && chat.other_plan_id === planId)

// A made-up chat API for one check. It lists the chats it holds for the plan or pair asked, newest
// first, makes a chat for a first question, keeping a pair lowest id first as the API does, and
// answers each question as the check says. It records each list asked for, each chat made and each
// question sent.
async function madeUpChats(page: Page, held: MadeUpChats = {}) {
  const chats = [...(held.chats ?? [])]
  const messages: Record<string, Message[]> = { ...held.messages }
  const asked = { lists: [] as string[], started: [] as unknown[], sent: [] as Question[] }
  const answer: NonNullable<MadeUpChats['answer']> = held.answer ?? (() => ({ reply: messageOf('assistant', 'A made-up reply.') }))
  await page.route(chatRequests, async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const chatId = url.pathname.split('/').at(3)
    if (chatId === undefined && request.method() === 'GET') {
      asked.lists.push(url.search)
      const listed = chats.filter((chat) => holds(chat, url.searchParams.get('plan_id'), url.searchParams.get('other_plan_id')))
      return route.fulfill({ json: listed, headers: allowed })
    }
    if (chatId === undefined) {
      const body = request.postDataJSON() as { plan_id: string; other_plan_id: string | null }
      asked.started.push(body)
      const other = body.other_plan_id
      const [low, high] = other !== null && other < body.plan_id ? [other, body.plan_id] : [body.plan_id, other]
      const chat: Chat = { ...chatOf(low), other_plan_id: high }
      chats.unshift(chat)
      messages[chat.id] = []
      return route.fulfill({ status: 201, json: chat, headers: allowed })
    }
    if (request.method() === 'GET') return route.fulfill({ json: messages[chatId] ?? [], headers: allowed })
    const body = request.postDataJSON() as { content: string; term: string }
    asked.sent.push({ chatId, ...body })
    const answered = await answer({ chatId, ...body })
    if ('refusal' in answered) return refuse(route, answered.refusal)
    const reply = 'reply' in answered ? answered.reply : messageOf('assistant', 'A made-up reply, saved before the drop.')
    const exchange = { question: messageOf('user', body.content), reply }
    if (!('drop' in answered) || answered.drop === 'saved') {
      messages[chatId] = [...(messages[chatId] ?? []), exchange.question, exchange.reply]
    }
    if ('drop' in answered) return route.abort('failed')
    const chat = chats.find((each) => each.id === chatId)
    if (chat && answered.title) chat.title = answered.title
    return route.fulfill({ status: 201, json: exchange, headers: allowed })
  })
  return asked
}

const rail = (page: Page) => page.getByRole('complementary', { name: 'Assistant' })
const conversation = (page: Page) => page.getByRole('log', { name: 'Conversation' })
const chatBox = (page: Page) => page.getByRole('textbox', { name: 'Ask SAGE' })
const button = (page: Page, name: string) => page.getByRole('button', { name, exact: true })

// /plan as it opens her first plan, once the plan has arrived and faded in: her set, as the page read
// it, and the plan's id. It starts from a blank page, as the page before, such as a parity case's
// Course History, may still be reading her set, and that answer's body is gone once /plan replaces it.
async function herPlan(page: Page): Promise<{ set: PlanSet; planId: string }> {
  await page.goto('about:blank')
  const read = page.waitForResponse((response) => new URL(response.url()).pathname === '/v1/plans')
  await page.goto('/plan')
  const set = (await (await read).json()) as PlanSet
  await page.waitForURL(planAddress)
  await settledArrival(page)
  await settled(page)
  return { set, planId: new URL(page.url()).pathname.replace('/plan/', '') }
}

const nameOf = (set: PlanSet, planId: string) => set.plans.find((plan) => plan.id === planId)?.name

// The mouse moved off the page's controls. Opening the assistant leaves it over Collapse Assistant,
// whose tooltip would fade in under axe, which counts half-faded text as too faint, and over a
// photograph of anything but a hover.
const rest = (page: Page) => page.mouse.move(0, 0)

async function openAssistant(page: Page): Promise<void> {
  await button(page, 'Open Assistant').click()
  await rest(page)
  await chatBox(page).waitFor()
}

async function ask(page: Page, question: string): Promise<void> {
  await chatBox(page).fill(question)
  await chatBox(page).press('Enter')
}

test("the chat follows the address: a plan's own, then the pair's, whose first question makes its chat with both plans", async ({
  page,
}) => {
  const { set, planId } = await herPlan(page)
  const chat = chatOf(planId)
  const asked = await madeUpChats(page, {
    chats: [chat],
    messages: { [chat.id]: [messageOf('user', 'A question about this plan'), messageOf('assistant', 'An answer about this plan.')] },
  })
  await openAssistant(page)
  await expect(conversation(page)).toContainText('An answer about this plan.')
  await expect(rail(page)).toContainText(`Reading ${nameOf(set, planId)}`)
  expect(asked.lists).toEqual([`?plan_id=${planId}`])

  await button(page, 'Compare').click()
  await page.waitForURL(/\?compare=/)
  const partner = new URL(page.url()).searchParams.get('compare')
  await expect(rail(page)).toContainText(`Comparing ${nameOf(set, planId)} and ${nameOf(set, partner ?? '')}`)
  // The pair has no chat yet, so it offers the questions to start from
  await button(page, 'How do these plans differ?').click()
  await expect(conversation(page)).toContainText('A made-up reply.')
  expect(asked.lists[1]).toBe(`?plan_id=${planId}&other_plan_id=${partner}`)
  expect(asked.started).toEqual([{ plan_id: planId, other_plan_id: partner }])
  expect(asked.sent.map(({ content, term }) => ({ content, term }))).toEqual([{ content: 'How do these plans differ?', term: 'sem1' }])
})

test('a reply shows its numbered sources, the line to her student advisor and Open Plan, and a plan her answers hid that it offers joins her plans', async ({
  page,
}) => {
  const { set, planId } = await herPlan(page)
  const open = set.plans.find((plan) => plan.id === planId)
  const hidden = set.plans.find((plan) => plan.hidden)
  if (!open || !hidden) throw new Error("Mbali's seed opens a kept plan first and hides three")
  // Her set as the API reads it, showing the offered plan once the reply is saved, as the chats
  // service does
  let replied = false
  await page.route('**/v1/plans', async (route) => {
    const response = await route.fetch()
    const read = (await response.json()) as PlanSet
    const plans = read.plans.map((plan) => (plan.id === hidden.id ? { ...plan, hidden: !replied } : plan))
    await route.fulfill({ response, json: { ...read, plans } })
  })
  await madeUpChats(page, {
    answer: () => {
      replied = true
      return { reply: messageOf('assistant', clashFree, { citations: sources, referral: true, open_plan_id: hidden.id }) }
    },
  })
  await openAssistant(page)
  await ask(page, 'Is this plan clash-free?')
  await expect(page.getByRole('list', { name: 'Sources' }).getByRole('listitem')).toHaveCount(2)
  await expect(rail(page).getByText('Your student advisor can help with this.')).toBeVisible()
  // In her plan list at once, with no reload
  await page.getByRole('button', { name: open.name }).click()
  await expect(page.getByRole('option', { name: hidden.name })).toBeVisible()
  await page.keyboard.press('Escape')
  await page.getByRole('link', { name: `Open ${hidden.name}` }).click()
  await page.waitForURL(`**/plan/${hidden.id}`)
  // Now one of the plans she switches between, so the switcher names it
  await expect(page.getByRole('button', { name: hidden.name })).toBeVisible()
})

test('advisor_unavailable keeps her question and says why, and Try Again sends the same words to the same chat', async ({
  page,
}) => {
  await herPlan(page)
  let tries = 0
  const asked = await madeUpChats(page, {
    answer: () => {
      tries += 1
      return tries === 1 ? { refusal: refusalOf('advisor_unavailable', 503) } : { reply: messageOf('assistant', 'A made-up answer.') }
    },
  })
  await openAssistant(page)
  await ask(page, 'Which day is my busiest?')
  await expect(rail(page).getByText("The Assistant Couldn't Reply")).toBeVisible()
  await expect(conversation(page)).toContainText('Which day is my busiest?')

  await button(page, 'Try Again').click()
  await expect(conversation(page)).toContainText('A made-up answer.')
  await expect(rail(page).getByText("The Assistant Couldn't Reply")).toHaveCount(0)
  // One chat, made by the first try, and the same question sent to it twice
  expect(asked.started).toHaveLength(1)
  expect(asked.sent).toHaveLength(2)
  expect(asked.sent[1]).toEqual(asked.sent[0])
})

test('while a reply is on its way, Enter sends nothing more and the next question waits in the box', async ({ page }) => {
  await herPlan(page)
  let reply = () => {}
  const replied = new Promise<void>((resolve) => {
    reply = resolve
  })
  const asked = await madeUpChats(page, {
    answer: async () => {
      await replied
      return { reply: messageOf('assistant', 'A made-up answer to the first.') }
    },
  })
  await openAssistant(page)
  await ask(page, 'The first question')
  await expect(rail(page).getByText('Working on your answer…')).toBeVisible()
  await ask(page, 'The second question')
  await expect(button(page, 'Send')).toBeDisabled()

  reply()
  await expect(conversation(page)).toContainText('A made-up answer to the first.')
  // Had the second gone, it would have been asked before the first was answered
  expect(asked.sent.map(({ content }) => content)).toEqual(['The first question'])
  await expect(chatBox(page)).toHaveValue('The second question')
  await expect(button(page, 'Send')).toBeEnabled()
})

test("a question on its way in a plan holds Send there alone: the pair's question goes, and the plan's reply still lands", async ({
  page,
}) => {
  await herPlan(page)
  let reply = () => {}
  const replied = new Promise<void>((resolve) => {
    reply = resolve
  })
  const asked = await madeUpChats(page, {
    // Only the plan's question waits for its reply
    answer: async ({ content }) => {
      if (content === 'A question about the plan') await replied
      return { reply: messageOf('assistant', `A made-up answer to ${content.toLowerCase()}.`) }
    },
  })
  await openAssistant(page)
  await ask(page, 'A question about the plan')
  await expect(rail(page).getByText('Working on your answer…')).toBeVisible()

  await button(page, 'Compare').click()
  // The pair's empty chat offers its question only when nothing holds Send there
  await button(page, 'How do these plans differ?').waitFor()
  await ask(page, 'A question about the pair')
  await expect(conversation(page)).toContainText('A made-up answer to a question about the pair.')

  await button(page, 'Done Comparing').click()
  await page.waitForURL((url) => !url.searchParams.has('compare'))
  // The plan's question still waits where she left it
  await expect(conversation(page)).toContainText('A question about the plan')
  await expect(rail(page).getByText('Working on your answer…')).toBeVisible()
  reply()
  await expect(conversation(page)).toContainText('A made-up answer to a question about the plan.')
  expect(asked.sent.map(({ content }) => content)).toEqual(['A question about the plan', 'A question about the pair'])
})

test("the chat list is read again after a reply, so the advisor's title replaces New Chat", async ({ page }) => {
  const { planId } = await herPlan(page)
  const chat = chatOf(planId)
  await madeUpChats(page, {
    chats: [chat],
    messages: { [chat.id]: [messageOf('user', 'A first question'), messageOf('assistant', 'A first answer.')] },
    answer: () => ({ reply: messageOf('assistant', 'A second answer.'), title: 'Made-up Title' }),
  })
  await openAssistant(page)
  await button(page, 'Chat History').click()
  await expect(page.getByRole('menuitemradio', { name: 'New Chat' })).toBeVisible()
  await page.keyboard.press('Escape')

  await ask(page, 'A second question')
  await expect(conversation(page)).toContainText('A second answer.')
  await button(page, 'Chat History').click()
  await expect(page.getByRole('menuitemradio', { name: 'Made-up Title' })).toBeVisible()
})

test('a question cut off on its way is checked against the chat: saved, its reply shows; lost, the error and Try Again', async ({
  page,
}) => {
  await herPlan(page)
  let tries = 0
  await madeUpChats(page, {
    answer: () => {
      tries += 1
      return { drop: tries === 1 ? 'saved' : 'lost' }
    },
  })
  await openAssistant(page)
  await ask(page, 'A question the API saved')
  await expect(conversation(page)).toContainText('A made-up reply, saved before the drop.')
  await expect(rail(page).getByText("Can't Reach SAGE")).toHaveCount(0)

  // The reply shows once the chat is read again, and Send waits until the chat list and her set are
  // too, so the next question goes once Send is ready, as she would send it
  await chatBox(page).fill('A question the API lost')
  await expect(button(page, 'Send')).toBeEnabled()
  await chatBox(page).press('Enter')
  await expect(rail(page).getByText("Can't Reach SAGE")).toBeVisible()
  await expect(button(page, 'Try Again')).toBeVisible()
})

test("at a plan's address the folded strip shows while her set is read, and goes once it says her set needs its questions answered", async ({
  page,
}) => {
  await herPlan(page)
  // Her set as the API gives it, but still needing its questions answered, once it's let go
  await page.route(read('/v1/plans'), async (route) => {
    const set = (await (await route.fetch()).json()) as PlanSet
    await route.fulfill({ json: { ...set, questionnaire_needed: true }, headers: allowed })
  })
  const set = await hold(page, read('/v1/plans'))
  await page.reload()
  await expect(button(page, 'Open Assistant')).toBeVisible()
  await set.release()
  await expect(rail(page)).toHaveCount(0)
})

test('open, the header shows at once over bubble-shaped skeletons, with Send held, until her chats arrive', async ({ page }, testInfo) => {
  const { set, planId } = await herPlan(page)
  const chat = chatOf(planId)
  await madeUpChats(page, {
    chats: [chat],
    messages: { [chat.id]: [messageOf('user', 'A question about this plan'), messageOf('assistant', clashFree)] },
  })
  const chats = await hold(page, read('/v1/chats'))
  await openAssistant(page)
  await expect(rail(page).getByRole('heading', { level: 2, name: 'Assistant' })).toBeVisible()
  await expect(rail(page)).toContainText(`Reading ${nameOf(set, planId)}`)
  await expect(button(page, 'New Chat')).toBeVisible()
  await expect(loading(page, 'Loading your chat…')).toBeAttached()
  await expect(skeletons(rail(page)).first()).toBeVisible()
  await chatBox(page).fill('A question while the chat loads')
  await expect(button(page, 'Send')).toBeDisabled()
  await expectNoAxeViolations(page)
  await chatBox(page).fill('')
  await photographArrival(page, testInfo, 'assistant', () => chats.release())
  await expect(conversation(page)).toContainText(clashFree)
})

test("in compare, the pair's name is a skeleton until the pair is read", async ({ page }, testInfo) => {
  const { set, planId } = await herPlan(page)
  await madeUpChats(page)
  await openAssistant(page)
  await settled(page)
  const pair = await hold(page, read('/v1/plans/compare'))
  await button(page, 'Compare').click()
  await page.waitForURL(/\?compare=/)
  await rest(page)
  const partner = new URL(page.url()).searchParams.get('compare') ?? ''
  await expect(skeletons(rail(page)).first()).toBeVisible()
  await expect(rail(page)).not.toContainText('Comparing')
  await expectNoAxeViolations(page)
  await photographArrival(page, testInfo, 'assistant-compare', () => pair.release())
  await expect(rail(page)).toContainText(`Comparing ${nameOf(set, planId)} and ${nameOf(set, partner)}`)
})

test('after a reply, her set is read again with no skeleton, no blank switcher and no fade', async ({ page }) => {
  await watchLoading(page)
  await herPlan(page)
  await madeUpChats(page)
  await openAssistant(page)
  await settled(page)
  const switcher = await page.getByRole('button', { name: /^Power, Control & Robotics/ }).elementHandle()
  await forgetSeen(page)
  const set = await hold(page, read('/v1/plans'))
  const readAgain = page.waitForRequest((request) => read('/v1/plans')(new URL(request.url())))
  await ask(page, 'Is this plan clash-free?')
  await expect(conversation(page)).toContainText('A made-up reply.')
  // Held, so the check sees the page while the read is on its way
  await readAgain
  await settled(page)
  expect(await seenLoading(page)).toEqual({ skeletons: 0, fades: 0 })
  expect(await switcher.evaluate((element) => element.isConnected)).toBe(true)
  await set.release()
})

test('Compare and the view toggle show only their icons while the sidebar and the assistant are both open', async ({ page }) => {
  await herPlan(page)
  await madeUpChats(page)
  const compare = button(page, 'Compare')
  const calendar = page.getByRole('radio', { name: 'Calendar' })
  await expect(compare).toHaveText('Compare')
  await openAssistant(page)
  await expect(compare).toHaveText('')
  await expect(calendar).toHaveText('')
  // The folded sidebar leaves them room
  await button(page, 'Collapse Sidebar').click()
  await expect(compare).toHaveText('Compare')
  await expect(calendar).toHaveText('Calendar')
  await button(page, 'Open Sidebar').click()
  await expect(compare).toHaveText('')
  // And so does the folded assistant
  await button(page, 'Collapse Assistant').click()
  await expect(compare).toHaveText('Compare')
})

test('opening and folding the assistant by keyboard leaves focus on the toggle that replaced the one pressed', async ({ page }) => {
  await herPlan(page)
  await madeUpChats(page)
  await button(page, 'Open Assistant').focus()
  await page.keyboard.press('Enter')
  await expect(button(page, 'Collapse Assistant')).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(button(page, 'Open Assistant')).toBeFocused()
})

// The folded assistant passes axe on her plan's page in routes.spec.ts
test('the open assistant, an empty chat and its empty history pass axe', async ({ page }) => {
  test.setTimeout(90_000)
  await herPlan(page)
  await madeUpChats(page)
  await openAssistant(page)
  await expectNoAxeViolations(page)
  await button(page, 'Chat History').click()
  await settled(page)
  await expectNoAxeViolations(page)
})

test('a reply with its sources and Open Plan, and the history listing its chat, pass axe, and the keyboard walks the assistant', async ({
  page,
}) => {
  test.setTimeout(90_000)
  const { set, planId } = await herPlan(page)
  const other = set.plans.find((plan) => plan.id !== planId)
  if (!other) throw new Error("Mbali's seed has ten plans")
  const chat = chatOf(planId, 'Is This Plan Clash-Free')
  const reply = messageOf('assistant', clashFree, { citations: sources, referral: true, open_plan_id: other.id })
  await madeUpChats(page, { chats: [chat], messages: { [chat.id]: [messageOf('user', 'Is this plan clash-free?'), reply] } })
  await openAssistant(page)
  await expect(conversation(page)).toContainText(clashFree)
  await expectNoAxeViolations(page)
  await walkKeyboard(page)
  await button(page, 'Chat History').click()
  await settled(page)
  await expectNoAxeViolations(page)
})

test('the wait for a reply and a reply that failed pass axe', async ({ page }) => {
  test.setTimeout(90_000)
  await herPlan(page)
  let reply = () => {}
  const replied = new Promise<void>((resolve) => {
    reply = resolve
  })
  await madeUpChats(page, {
    answer: async () => {
      await replied
      return { refusal: refusalOf('advisor_unavailable', 503) }
    },
  })
  await openAssistant(page)
  await ask(page, 'Is this plan clash-free?')
  await expect(rail(page).getByText('Working on your answer…')).toBeVisible()
  await expectNoAxeViolations(page)
  reply()
  await expect(button(page, 'Try Again')).toBeVisible()
  await expectNoAxeViolations(page)
})

test.describe('parity', () => {
  // The planner prototype at its plan, reached through its own questions with Mechatronics chosen, as
  // PlanView.spec.ts reaches it, in the run's theme. Its assistant starts folded, as SAGE's does.
  async function prototypePlan(page: Page, theme: Theme): Promise<void> {
    if (theme === 'dark') await page.goto(`${page.url()}?theme=dark`)
    await button(page, 'Create registration plan').click()
    await page.getByRole('button', { name: 'Mechatronics', exact: true }).click()
    await button(page, 'Generate plans').click()
    await settled(page)
  }

  // The prototype's assistant opened from its rail
  async function prototypeOpen(page: Page): Promise<void> {
    await button(page, 'Open assistant').click()
    await rest(page)
    await settled(page)
  }

  // The prototype's assistant, open, after asking its first suggested question, whose answer comes
  // after a made-up wait
  async function prototypeReply(page: Page): Promise<void> {
    await button(page, 'Open assistant').click()
    await button(page, 'Is this plan clash-free?').click()
    await rest(page)
    await page.getByText(clashFree).waitFor()
    await settled(page)
  }

  const designedRail = (page: Page) => button(page, 'Collapse assistant').locator('xpath=ancestor::aside[1]')
  // Its plan area is four divs up from its plan switcher, whose name stays when Compare's goes
  const designedPlan = (page: Page) => page.getByRole('button', { name: /^Power & Robotics/ }).first().locator('xpath=ancestor::div[4]')
  // The loading and error sheets draw each assistant case in light, then in dark: the panel three divs
  // up from her question
  const inSheet = (page: Page, theme: Theme) =>
    page
      .getByText('Is this plan clash-free?', { exact: true })
      .nth(theme === 'dark' ? 1 : 0)
      .locator('xpath=ancestor::div[3]')

  // The React side: her plan as /plan opens it, with made-up chats, as a case needs them
  async function builtRail(page: Page, held: (plan: { set: PlanSet; planId: string }) => MadeUpChats = () => ({})) {
    const plan = await herPlan(page)
    await madeUpChats(page, held(plan))
    await openAssistant(page)
    await settled(page)
  }

  // Compare from her plan, with the mouse moved off its button, which would show its tooltip
  async function builtCompare(page: Page): Promise<void> {
    await button(page, 'Compare').click()
    await page.waitForURL(/\?compare=/)
    await rest(page)
  }

  // Her plan's chat holding the prototype's question and answer, with the API's sources, the line to
  // her student advisor and Open Plan, offering another of her plans, and the advisor's title
  const answered = ({ set, planId }: { set: PlanSet; planId: string }): MadeUpChats => {
    const chat = chatOf(planId, 'Is This Plan Clash-Free')
    const offered = set.plans.find((plan) => plan.id !== planId)?.id ?? null
    const reply = messageOf('assistant', clashFree, { citations: sources, referral: true, open_plan_id: offered })
    return { chats: [chat], messages: { [chat.id]: [messageOf('user', 'Is this plan clash-free?'), reply] } }
  }

  // The question on its way: the made-up advisor never answers
  const waiting: MadeUpChats = { answer: () => new Promise<Answer>(() => {}) }
  const failing: MadeUpChats = { answer: () => ({ refusal: refusalOf('advisor_unavailable', 503) }) }

  function state(name: string, designed: ParityCase['reach'], built: (page: Page) => Promise<void>, element: ParityCase['react']['element'], hover = false): ParityCase {
    return { name, prototype: 'registration-planner', reach: designed, react: { path: '/history', reach: built, element }, hover }
  }

  parity('assistant', [
    state(
      'folded',
      async (page, theme) => {
        await prototypePlan(page, theme)
        return button(page, 'Open assistant').locator('..')
      },
      async (page) => {
        await herPlan(page)
        await settled(page)
      },
      rail,
    ),
    state(
      'open',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await prototypeOpen(page)
        return designedRail(page)
      },
      (page) => builtRail(page),
      rail,
    ),
    state(
      'compare',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await button(page, 'Compare').click()
        await prototypeOpen(page)
        return designedRail(page)
      },
      async (page) => {
        await builtRail(page)
        await builtCompare(page)
        await button(page, 'How do these plans differ?').waitFor()
        await settled(page)
      },
      rail,
    ),
    state(
      'reply',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await prototypeReply(page)
        return designedRail(page)
      },
      async (page) => {
        await builtRail(page, answered)
        await conversation(page).getByText(clashFree).waitFor()
      },
      rail,
    ),
    state(
      'history',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await prototypeReply(page)
        await button(page, 'Chat history').click()
        await settled(page)
        return page.getByText('Chats in this view').locator('..')
      },
      async (page) => {
        await builtRail(page, answered)
        await button(page, 'Chat History').click()
        await settled(page)
      },
      (page) => page.getByRole('menu').locator('..'),
    ),
    state(
      'history-empty',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await prototypeOpen(page)
        await button(page, 'Chat history').click()
        await settled(page)
        return page.getByText('No chats yet in this view.').locator('..')
      },
      async (page) => {
        await builtRail(page)
        await button(page, 'Chat History').click()
        await settled(page)
      },
      (page) => page.getByRole('menu').locator('..'),
    ),
    {
      name: 'waiting',
      prototype: 'loading-states',
      reach: async (page, theme) => {
        await settled(page)
        return inSheet(page, theme)
      },
      react: {
        path: '/history',
        reach: async (page) => {
          await builtRail(page, () => waiting)
          await ask(page, 'Is this plan clash-free?')
          await page.getByText('Working on your answer…').waitFor()
          await settled(page)
        },
        element: rail,
      },
    },
    {
      name: 'error',
      prototype: 'error-states',
      reach: async (page, theme) => {
        await settled(page)
        return inSheet(page, theme)
      },
      react: {
        path: '/history',
        reach: async (page) => {
          await builtRail(page, () => failing)
          await ask(page, 'Is this plan clash-free?')
          await button(page, 'Try Again').waitFor()
          await settled(page)
        },
        element: rail,
      },
    },
    state(
      'icon-only',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await prototypeOpen(page)
        return designedPlan(page)
      },
      (page) => builtRail(page),
      (page) => page.getByRole('main'),
    ),
    state(
      'icon-only-compare',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await button(page, 'Compare').click()
        await prototypeOpen(page)
        return page.getByText('Comparing plans').locator('xpath=ancestor::div[3]')
      },
      async (page) => {
        await builtRail(page)
        await builtCompare(page)
        await page.getByRole('heading', { level: 2 }).first().waitFor()
        await settled(page)
      },
      (page) => page.getByRole('main'),
    ),
    state(
      'open-assistant',
      async (page, theme) => {
        await prototypePlan(page, theme)
        return button(page, 'Open assistant')
      },
      async (page) => {
        await herPlan(page)
        await settled(page)
      },
      (page) => button(page, 'Open Assistant'),
      true,
    ),
    ...(
      [
        ['new-chat', 'New chat', 'New Chat'],
        ['chat-history', 'Chat history', 'Chat History'],
        ['collapse-assistant', 'Collapse assistant', 'Collapse Assistant'],
        ['suggestion', 'Can I swap an elective?', 'Can I swap an elective?'],
      ] as const
    ).map(([name, designedName, builtName]) =>
      state(
        name,
        async (page, theme) => {
          await prototypePlan(page, theme)
          await prototypeOpen(page)
          return button(page, designedName)
        },
        (page) => builtRail(page),
        (page) => button(page, builtName),
        true,
      ),
    ),
    state(
      'chat-row',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await prototypeReply(page)
        await button(page, 'Chat history').click()
        await settled(page)
        return page.getByText('Chats in this view').locator('..').getByRole('button')
      },
      async (page) => {
        await builtRail(page, answered)
        await button(page, 'Chat History').click()
        await settled(page)
      },
      (page) => page.getByRole('menuitemradio', { name: 'Is This Plan Clash-Free' }),
      true,
    ),
    {
      name: 'try-again',
      prototype: 'error-states',
      reach: async (page, theme) => {
        await settled(page)
        return inSheet(page, theme).getByText('Retry', { exact: true })
      },
      react: {
        path: '/history',
        reach: async (page) => {
          await builtRail(page, () => failing)
          await ask(page, 'Is this plan clash-free?')
          await button(page, 'Try Again').waitFor()
          await settled(page)
        },
        element: (page) => button(page, 'Try Again'),
      },
      hover: true,
    },
    state(
      'compare-icon',
      async (page, theme) => {
        await prototypePlan(page, theme)
        await prototypeOpen(page)
        // Icon-only, it has no name: the last button in the plan's header row
        return page.getByRole('button', { name: /^Power & Robotics/ }).first().locator('xpath=ancestor::div[3]').getByRole('button').last()
      },
      (page) => builtRail(page),
      (page) => button(page, 'Compare'),
      true,
    ),
  ])
})
