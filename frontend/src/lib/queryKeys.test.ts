// Which cached reads each change refreshes, against lists written out by hand from the foundations
// brief's refresh rules
import type { QueryKey } from '@tanstack/react-query'
import { afterEach, expect, it } from 'vitest'
import { queryClient } from './queryClient.ts'
import { queries, refresh } from './queryKeys.ts'

// Made-up ids
const plan = '00000000-0000-4000-8000-000000000001'
const otherPlan = '00000000-0000-4000-8000-000000000002'
const chat = '00000000-0000-4000-8000-000000000003'
const otherChat = '00000000-0000-4000-8000-000000000004'

// One cached read for every query, as the screens would leave them
const reads: Record<string, QueryKey> = {
  me: queries.me().queryKey,
  plans: queries.plans().queryKey,
  plan: queries.plan(plan).queryKey,
  preview: queries.preview(plan, 'SLL1002S').queryKey,
  comparison: queries.comparison(plan, otherPlan).queryKey,
  questionnaire: queries.questionnaire().queryKey,
  electives: queries.electives().queryKey,
  history: queries.history().queryKey,
  catalogue: queries.catalogue().queryKey,
  chats: queries.chats(plan).queryKey,
  pairChats: queries.chats(plan, otherPlan).queryKey,
  messages: queries.messages(chat).queryKey,
  otherMessages: queries.messages(otherChat).queryKey,
}

afterEach(() => {
  queryClient.clear()
})

it.each([
  ['answering the questionnaire', () => refresh.questionnaireAnswered(), ['plans', 'plan', 'preview', 'comparison']],
  ['a favourite', () => refresh.favouriteChanged(), ['questionnaire', 'electives']],
  ['starting a chat', () => refresh.chatStarted(), ['chats', 'pairChats']],
  ['a sent message', () => refresh.messageSent(chat), ['plans', 'chats', 'pairChats', 'messages']],
  ['Finish Setup', () => refresh.setupFinished(), ['me', 'plans']],
])('%s refreshes exactly its reads', async (_, change, expected) => {
  for (const queryKey of Object.values(reads)) queryClient.setQueryData(queryKey, {})

  await change()

  const refreshed = Object.keys(reads).filter((name) => queryClient.getQueryState(reads[name])?.isInvalidated)
  expect(refreshed).toEqual(expected)
})
