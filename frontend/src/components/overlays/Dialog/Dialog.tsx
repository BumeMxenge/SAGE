// A dialog over the page, shown while it is rendered. Escape, the close button and a click outside all
// call onClose, and focus stays inside it while it is open.
import type { ReactNode } from 'react'
import { Dialog as AriaDialog, Heading, Modal, ModalOverlay } from 'react-aria-components'
import { IconButton } from '@/components/actions/IconButton/IconButton.tsx'
import styles from './Dialog.module.css'

type DialogProps = {
  title: string
  onClose: () => void
  children: ReactNode
}

export function Dialog({ title, onClose, children }: DialogProps) {
  return (
    <ModalOverlay
      isOpen
      onOpenChange={(isOpen) => {
        if (!isOpen) onClose()
      }}
      isDismissable
      className={styles.overlay}
    >
      <Modal className={styles.modal}>
        <AriaDialog className={styles.dialog}>
          {({ close }) => (
            <>
              <div className={styles.header}>
                <Heading slot="title" className={styles.title}>
                  {title}
                </Heading>
                <IconButton label="Close" icon="close" onPress={close} />
              </div>
              {children}
            </>
          )}
        </AriaDialog>
      </Modal>
    </ModalOverlay>
  )
}
