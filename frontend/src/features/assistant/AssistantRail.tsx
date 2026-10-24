// The assistant, docked beside the plan at a plan's own address: the named aside approved difference
// 6 asks for. Folded, it's a strip holding Open Assistant, an icon button, with Assistant written up
// the strip under it, as in the prototype. Open, its header names the plan or pair the address puts
// on screen, and their chat fills the rest: the newest, the one she picked from Chat History, or a new
// one. A new chat is made only as its first question goes, so New Chat leaves none behind. The
// questions being answered are kept here, one for each plan and pair, not in the chat, so folding the
// assistant or moving between chats keeps them. Each plan and pair answers one at a time, as two
// questions in one chat at once would each be answered without seeing the other, but a question on
// its way in one doesn't hold another. There's no assistant while her set still needs its questions answered, as the API keeps
// chats closed then and the prototype shows the assistant only beside an open plan, nor beside a plan
// that doesn't exist. Pressing a toggle moves focus to the one that replaces it, as the sidebar's do,
// and what is folded away isn't there to take focus.
import { useIsMutating, useMutation, useMutationState, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { IconButton } from '@/components/actions/IconButton/IconButton.tsx'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import { Menu } from '@/components/overlays/Menu/Menu.tsx'
import { MenuItem } from '@/components/overlays/Menu/MenuItem.tsx'
import { MenuSection } from '@/components/overlays/Menu/MenuSection.tsx'
import { ApiError, client, dataOf, type ErrorCode } from '@/lib/api.ts'
import { type PlanTerm, usePlanAddress } from '@/lib/planAddress.ts'
import { queryClient } from '@/lib/queryClient.ts'
import { queries, refresh } from '@/lib/queryKeys.ts'
import { Conversation } from './components/Conversation/Conversation.tsx'
import styles from './AssistantRail.module.css'

// A question sent about one plan or pair, with the chat it goes to: none for a new chat, until the
// chat is made
type Turn = {
  scope: string
  planId: string
  otherPlanId: string | null
  chatId: string | null
  content: string
  term: PlanTerm
}

// The failures that can't say whether the question and its reply were stored: no connection, no answer
// in time, a gateway's page, or a server error, which can come after the exchange is saved
const unsure: ErrorCode[] = ['network_error', 'timeout', 'server_unavailable', 'internal_error']

// A key for each plan and pair, so a question on its way holds Send in its own view alone
const turnKey = (scope: string) => ['turn', scope]

type AssistantRailProps = { open: boolean; onOpenChange: (open: boolean) => void }

export function AssistantRail({ open, onOpenChange }: AssistantRailProps) {
  const { planId, compareWith, term } = usePlanAddress()
  // A pair is the same pair in either order, as the API keeps it
  const scope = compareWith === null ? planId : [planId, compareWith].sort().join(' ')
  // Only after a toggle press, never as a page opens
  const [moveFocus, setMoveFocus] = useState(false)
  // The chat open on each plan and pair: one she picked, or null for a new one. Unset, the newest.
  const [picked, setPicked] = useState<Partial<Record<string, string | null>>>({})
  // The question last sent from each plan and pair, with its chat once that's made
  const [turns, setTurns] = useState<Partial<Record<string, Turn>>>({})
  // The plan or pair on screen, from the reads the plan view makes
  const single = useQuery({ ...queries.plan(planId), enabled: compareWith === null })
  const pair = useQuery({ ...queries.comparison(planId, compareWith ?? planId), enabled: compareWith !== null })
  const { data: set } = useQuery(queries.plans())
  const chats = useQuery({ ...queries.chats(planId, compareWith ?? undefined), enabled: open })
  const waiting = useIsMutating({ mutationKey: turnKey(scope) }) > 0
  const asking = useMutation({
    mutationKey: turnKey(scope),
    mutationFn: ask,
    // The question and its reply join the chat, the reply may bring the chat its first title, and a
    // plan it offers joins her plan list. Her question stays on screen until they arrive.
    onSuccess: (chatId) => refresh.messageSent(chatId),
    // Kept until she reloads: a finished question nothing watches is otherwise dropped after five
    // minutes, taking with it a failure she left in another view
    gcTime: Infinity,
  })
  // How this view's last question went, from the cache, as asking follows only the latest anywhere
  const outcome = useMutationState({ filters: { mutationKey: turnKey(scope) }, select: (mutation) => mutation.state }).at(-1)

  const error = compareWith === null ? single.error : pair.error
  if (error instanceof ApiError && error.code === 'plan_not_found') return null
  // Nothing until her set is read, as the plan view waits for it too, and nothing while it still needs
  // its questions answered
  if (!set || set.questionnaire_needed) return null

  // Sends a question, first making its chat if it has none, and gives back the chat it went to
  async function ask(question: Turn): Promise<string> {
    const chatId = question.chatId ?? (await start(question))
    const before = queryClient.getQueryData(queries.messages(chatId).queryKey)?.length ?? 0
    try {
      await dataOf(
        client.POST('/v1/chats/{chat_id}/messages', {
          params: { path: { chat_id: chatId } },
          body: { content: question.content, term: question.term },
        }),
      )
    } catch (failure) {
      // A failure that can't say what was stored is checked against the chat itself, so a question
      // already answered isn't offered again
      if (!(failure instanceof ApiError) || !unsure.includes(failure.code)) throw failure
      const after = await queryClient.fetchQuery({ ...queries.messages(chatId), staleTime: 0 })
      if (after.length <= before) throw failure
    }
    return chatId
  }

  async function start(question: Turn): Promise<string> {
    const chat = await dataOf(client.POST('/v1/chats', { body: { plan_id: question.planId, other_plan_id: question.otherPlanId } }))
    // A new chat has no messages, so it opens at once, her question still showing, with nothing to read
    queryClient.setQueryData(queries.messages(chat.id).queryKey, [])
    // The assistant follows the new chat, and Try Again goes to it
    setPicked((before) => ({ ...before, [question.scope]: chat.id }))
    setTurns((before) => ({ ...before, [question.scope]: { ...question, chatId: chat.id } }))
    await refresh.chatStarted()
    return chat.id
  }

  function toggle() {
    onOpenChange(!open)
    setMoveFocus(true)
  }

  const pick = (chatId: string | null) => setPicked((before) => ({ ...before, [scope]: chatId }))
  const chosen = picked[scope]
  const chatId = chosen === undefined ? (chats.data?.at(0)?.id ?? null) : chosen

  function send(content: string) {
    const question = { scope, planId, otherPlanId: compareWith, chatId, content, term }
    setTurns((before) => ({ ...before, [scope]: question }))
    asking.mutate(question)
  }

  const turn = turns[scope]

  function retry() {
    if (turn) asking.mutate(turn)
  }

  // This chat's question, while it waits or once it failed
  const sent =
    turn !== undefined && turn.chatId === chatId && (outcome?.status === 'pending' || outcome?.status === 'error')
      ? { content: turn.content, error: outcome.error }
      : null
  // The open plan's name, or null for a pair. Undefined until the plan is read.
  const planName = compareWith === null ? single.data?.name : null
  const reading =
    compareWith === null
      ? single.data && `Reading ${single.data.name}`
      : pair.data && `Comparing ${pair.data.first.name} and ${pair.data.second.name}`

  return (
    <aside aria-label="Assistant" data-folded={!open || undefined} className={styles.rail}>
      {open ? (
        <>
          <header className={styles.header}>
            <Icon name="chat_bubble" />
            <div className={styles.heading}>
              <h2 className={styles.title}>Assistant</h2>
              {reading && <p className={styles.reading}>{reading}</p>}
            </div>
            {chats.data && (
              <>
                <IconButton label="New Chat" icon="border_color" onPress={() => pick(null)} />
                <Menu
                  label="Chat History"
                  empty="No chats yet in this view."
                  trigger={<IconButton label="Chat History" icon="history" />}
                >
                  {chats.data.length > 0 && (
                    // Each chat opens on its own press; the section only shows which is open
                    <MenuSection
                      title="Chats in This View"
                      selectionMode="single"
                      selectedKeys={chatId === null ? [] : [chatId]}
                    >
                      {chats.data.map((chat) => (
                        <MenuItem key={chat.id} id={chat.id} icon="chat_bubble" onAction={() => pick(chat.id)}>
                          {chat.title ?? 'New Chat'}
                        </MenuItem>
                      ))}
                    </MenuSection>
                  )}
                </Menu>
              </>
            )}
            <IconButton
              label="Collapse Assistant"
              icon="chevron_right"
              // Only after a toggle press, never as a page opens: see moveFocus
              // oxlint-disable-next-line jsx-a11y/no-autofocus
              autoFocus={moveFocus}
              onPress={toggle}
            />
          </header>
          {chats.data && planName !== undefined && (
            <Conversation
              chatId={chatId}
              address={{ planId, compareWith, term }}
              plans={set.plans}
              planName={planName}
              waiting={waiting}
              sent={sent}
              onSend={send}
              onRetry={retry}
            />
          )}
        </>
      ) : (
        <>
          <IconButton
            label="Open Assistant"
            icon="chat_bubble"
            // Only after a toggle press, never as a page opens: see moveFocus
            // oxlint-disable-next-line jsx-a11y/no-autofocus
            autoFocus={moveFocus}
            onPress={toggle}
          />
          {/* The aside and its button already say Assistant, so a screen reader doesn't hear it again */}
          <span aria-hidden="true" className={styles.label}>
            Assistant
          </span>
        </>
      )}
    </aside>
  )
}
