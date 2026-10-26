// A chat's skeleton while its chats or its messages are on their way, laid out as the conversation
// lays out an exchange: her question's bubble at the end of the line, then the reply's lines across
// the width. Each length is in characters.
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import styles from './Conversation.module.css'

const replyLines = [40, 42, 26]

export function ConversationSkeleton() {
  return (
    <div className={styles.waiting}>
      <span className={styles.bubble}>
        <Skeleton variant="block" />
      </span>
      <span className={styles.lines}>
        {replyLines.map((length) => (
          <span key={length}>
            <Skeleton variant="line" length={length} />
          </span>
        ))}
      </span>
    </div>
  )
}
