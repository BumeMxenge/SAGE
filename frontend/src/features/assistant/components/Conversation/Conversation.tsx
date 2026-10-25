// One chat with SAGE. Empty, it says what SAGE can help with and offers a question to start from.
// Otherwise its messages, oldest first: her questions in bubbles at the end of the line, and SAGE's
// replies across the width. A question on its way waits at the foot of the conversation, under the
// leaf saying SAGE is working, and one that failed says why where its reply would be, with Try Again
// when trying again can help. The conversation is a log, so a screen reader reads each new message as
// it arrives, and a tab stop, so the keyboard can scroll it (audit row 8). Sending in any way, and Try
// Again, leave focus in the chat box, as the button pressed may vanish or grey out under her. Until
// her chats say which is the newest, and the open chat's messages arrive, bubble-shaped skeletons hold
// the messages' place, and the chat box holds Send.
import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { Button } from '@/components/actions/Button/Button.tsx'
import { Arrival } from '@/components/feedback/Arrival/Arrival.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { LeafPulse } from '@/features/assistant/components/LeafPulse/LeafPulse.tsx'
import { ChatBox } from '@/features/assistant/components/ChatBox/ChatBox.tsx'
import { Reply } from '@/features/assistant/components/Reply/Reply.tsx'
import type { ApiError } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import { actionLabels, explain } from '@/lib/errors.ts'
import type { PlanAddress } from '@/lib/planAddress.ts'
import { queries } from '@/lib/queryKeys.ts'
import { ConversationSkeleton } from './ConversationSkeleton.tsx'
import styles from './Conversation.module.css'

type PlanSummary = components['schemas']['PlanSummary']

// A question this chat sent, while it waits for its reply or once it failed
type Sent = { content: string; error: ApiError | null }

type ConversationProps = {
  // null for a new chat, which has nothing to read until its first question, and undefined until her
  // chats say which is the newest
  chatId: string | null | undefined
  address: PlanAddress
  plans: PlanSummary[]
  planName: string | null // null for a pair
  waiting: boolean // a question on its way in this plan or pair, here or in its other chat, holds Send
  sent: Sent | null
  onSend: (question: string) => void
  onRetry: () => void
}

export function Conversation({ chatId, address, plans, planName, waiting, sent, onSend, onRetry }: ConversationProps) {
  const log = useRef<HTMLDivElement>(null)
  const box = useRef<HTMLTextAreaElement>(null)
  const read = useQuery({ ...queries.messages(chatId ?? ''), enabled: typeof chatId === 'string' })
  const messages = chatId === null ? [] : read.data
  // Her chats or this chat's messages still on their way
  const reading = chatId === undefined || (chatId !== null && read.isPending)
  const count = messages?.length

  // The newest message in view as each arrives, as a question goes and as one fails
  useEffect(() => {
    const end = log.current
    if (end) end.scrollTop = end.scrollHeight
  }, [chatId, count, sent?.content, sent?.error])

  function ask(question: string) {
    onSend(question)
    box.current?.focus()
  }

  function tryAgain() {
    onRetry()
    box.current?.focus()
  }

  const intro =
    planName === null
      ? 'I can compare these two plans: their courses, credits and timetables, and where they differ.'
      : `I can answer questions about ${planName}: its courses, credits and timetable, and the handbook rules behind them.`
  // One question each, whose answer changes from plan to plan. The prototype's others have the same
  // answer for every plan: the engine builds only clash-free plans, her plans carry about the same
  // load, and bursary renewal isn't in the handbook.
  const suggestion = planName === null ? 'How do these plans differ?' : 'Can I swap an elective?'
  const placeholder = planName === null ? 'Ask SAGE to compare these plans' : `Ask about ${planName}`
  const failure = sent?.error ? explain(sent.error) : null

  return (
    <div className={styles.conversation}>
      <Arrival
        // Each plan's, pair's and chat's messages are a read of their own
        key={`${address.planId} ${address.compareWith} ${chatId ?? ''}`}
        data={messages}
        waiting={reading}
        skeleton={<ConversationSkeleton />}
        status="Loading your chat…"
      >
        {(shown) => (
          <>
            {shown.length === 0 && sent === null && (
              <div className={styles.start}>
                <p className={styles.intro}>{intro}</p>
                {/* Left out while another of this view's chats waits for its reply, as nothing more can
                    go here */}
                {!waiting && (
                  <Button variant="suggestion" onPress={() => ask(suggestion)}>
                    {suggestion}
                  </Button>
                )}
              </div>
            )}
            {(shown.length > 0 || sent !== null) && (
              // A scrolling box must be a tab stop, or the keyboard can't scroll a conversation with
              // nothing to press
              // oxlint-disable-next-line jsx-a11y/no-noninteractive-tabindex
              <div ref={log} role="log" aria-label="Conversation" tabIndex={0} className={styles.log}>
                {shown.map((message) =>
                  message.role === 'user' ? (
                    <p key={message.id} className={styles.question}>
                      <span className="visually-hidden">You asked: </span>
                      {message.content}
                    </p>
                  ) : (
                    <Reply key={message.id} reply={message} plans={plans} address={address} />
                  ),
                )}
                {sent && (
                  <p className={styles.question}>
                    <span className="visually-hidden">You asked: </span>
                    {sent.content}
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </Arrival>
      {sent && sent.error === null && (
        <div className={styles.status}>
          <LeafPulse label="Working on your answer…" />
        </div>
      )}
      {failure && (
        <div className={styles.status}>
          <ErrorState variant="message" icon="error" title={failure.title} message={failure.message} reference={failure.reference}>
            {failure.action === 'retry' && (
              <Button variant="secondary" icon="refresh" onPress={tryAgain}>
                {actionLabels.retry}
              </Button>
            )}
          </ErrorState>
        </div>
      )}
      <div className={styles.box}>
        <ChatBox ref={box} label="Ask SAGE" placeholder={placeholder} held={messages === undefined} working={waiting} onSend={ask} />
      </div>
    </div>
  )
}
