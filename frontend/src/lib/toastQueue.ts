// The app's toasts, for background failures that don't block the page. Add one with
// toastQueue.add({ title: '…' }, { timeout: 5000 }). React Aria asks for at least 5 seconds, and
// pauses the timer while a toast is hovered or focused. Only a toast that can wait should time out.
// React Aria still marks its toast API UNSTABLE_, so this file and ToastRegion.tsx are the only places
// that name it.
import { UNSTABLE_ToastQueue as ToastQueue } from 'react-aria-components'

export type ToastContent = {
  title: string
  description?: string
  action?: { label: string; onPress: () => void }
}

export const toastQueue = new ToastQueue<ToastContent>()
