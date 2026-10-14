// Shows the toasts in toastQueue. Render it once, at the root of the app.
import {
  Button,
  Text,
  UNSTABLE_Toast as Toast,
  UNSTABLE_ToastContent as ToastContent,
  UNSTABLE_ToastRegion as AriaToastRegion,
} from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import { toastQueue } from '@/lib/toastQueue.ts'
import styles from './ToastRegion.module.css'

export function ToastRegion() {
  return (
    <AriaToastRegion queue={toastQueue} className={styles.region}>
      {({ toast }) => (
        <Toast toast={toast} className={styles.toast}>
          <ToastContent className={styles.content}>
            <Text slot="title" className={styles.title}>
              {toast.content.title}
            </Text>
            {toast.content.description && (
              <Text slot="description" className={styles.description}>
                {toast.content.description}
              </Text>
            )}
          </ToastContent>
          {toast.content.action && (
            <Button className={styles.action} onPress={toast.content.action.onPress}>
              {toast.content.action.label}
            </Button>
          )}
          <Button slot="close" aria-label="Close" className={styles.close}>
            <Icon name="close" />
          </Button>
        </Toast>
      )}
    </AriaToastRegion>
  )
}
