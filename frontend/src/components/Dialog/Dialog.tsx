// A dialog over the page. Escape, the close button and a click outside all close it, and focus stays
// inside it while it is open. Open it by setting isOpen; onOpenChange reports when it should close.
import type { ReactNode } from 'react'
import { Dialog as AriaDialog, Heading, Modal, ModalOverlay } from 'react-aria-components'
import { IconButton } from '@/components/IconButton/IconButton.tsx'
import styles from './Dialog.module.css'

type DialogProps = {
  title: string
  isOpen: boolean
  onOpenChange: (isOpen: boolean) => void
  children: ReactNode
}

export function Dialog({ title, isOpen, onOpenChange, children }: DialogProps) {
  return (
    <ModalOverlay isOpen={isOpen} onOpenChange={onOpenChange} isDismissable className={styles.overlay}>
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
