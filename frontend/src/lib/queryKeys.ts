// Every read's query, and what each change refreshes. openapi-react-query keys a read by its method,
// path and parameters, so each key here comes from its queryOptions, or, to refresh all of one
// endpoint's reads, from the start those keys share. A key written by hand could match no read, and
// its refresh would do nothing, silently. Screens read through these queries, so a read made in two
// places is cached and fetched once.
import { type QueryFunction, type QueryKey, queryOptions } from '@tanstack/react-query'
import createQueryHooks from 'openapi-react-query'
import type { paths } from './api-types.ts'
import { client } from './api.ts'
import { queryClient } from './queryClient.ts'

const openapi = createQueryHooks(client)

// openapi-react-query types a read's error as the API's problem body, but the middleware turns every
// failure into an ApiError. Built again from its key and function, each read takes TanStack Query's
// default error, which queryClient.ts registers as ApiError.
function read<TData, TKey extends QueryKey>({ queryKey, queryFn }: { queryKey: TKey; queryFn: QueryFunction<TData, TKey> }) {
  return queryOptions({ queryKey, queryFn })
}

export const queries = {
  me: () => read(openapi.queryOptions('get', '/v1/me')),
  plans: () => read(openapi.queryOptions('get', '/v1/plans')),
  plan: (planId: string) =>
    read(openapi.queryOptions('get', '/v1/plans/{plan_id}', { params: { path: { plan_id: planId } } })),
  // One course previewed in a plan's complementary slot
  preview: (planId: string, courseCode: string) =>
    read(
      openapi.queryOptions('get', '/v1/plans/{plan_id}/previews/{course_code}', {
        params: { path: { plan_id: planId, course_code: courseCode } },
      }),
    ),
  comparison: (first: string, second: string) =>
    read(openapi.queryOptions('get', '/v1/plans/compare', { params: { query: { first, second } } })),
  questionnaire: () => read(openapi.queryOptions('get', '/v1/questionnaire')),
  electives: () => read(openapi.queryOptions('get', '/v1/electives')),
  history: () => read(openapi.queryOptions('get', '/v1/history')),
  catalogue: () => read(openapi.queryOptions('get', '/v1/catalogue')),
  // The chats on one plan, or on a compared pair
  chats: (planId: string, otherPlanId?: string) =>
    read(openapi.queryOptions('get', '/v1/chats', { params: { query: { plan_id: planId, other_plan_id: otherPlanId } } })),
  messages: (chatId: string) =>
    read(openapi.queryOptions('get', '/v1/chats/{chat_id}/messages', { params: { path: { chat_id: chatId } } })),
}

// The start of the key of every read of one endpoint, whatever its parameters. The path is checked
// against api-types.ts, so a misspelt one fails the build.
const allOf = (path: keyof paths) => ['get', path] as const

async function refreshing(...keys: QueryKey[]): Promise<void> {
  await Promise.all(keys.map((queryKey) => queryClient.invalidateQueries({ queryKey })))
}

// What each change refreshes. A screen calls one once its change has saved.
export const refresh = {
  // The answers hide plans, and the plan set, each plan, each preview and each comparison say which
  // are hidden
  questionnaireAnswered: () =>
    refreshing(
      allOf('/v1/plans'),
      allOf('/v1/plans/{plan_id}'),
      allOf('/v1/plans/{plan_id}/previews/{course_code}'),
      allOf('/v1/plans/compare'),
    ),
  // A heart shows on its elective
  favouriteChanged: () => refreshing(allOf('/v1/electives')),
  // A new chat joins the list for its plan or pair
  chatStarted: () => refreshing(allOf('/v1/chats')),
  // The question and its reply join that chat, a reply can bring the chat its first title, and a plan
  // her answers hid joins her set's shown plans when a reply offers it
  messageSent: (chatId: string) => refreshing(queries.messages(chatId).queryKey, allOf('/v1/chats'), allOf('/v1/plans')),
  // Finish Setup completes the account and attaches its plans
  setupFinished: () => refreshing(queries.me().queryKey, allOf('/v1/plans')),
}
