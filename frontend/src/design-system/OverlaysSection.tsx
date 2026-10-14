import { useState } from 'react'
import { Button } from '@/components/Button/Button.tsx'
import { Dialog } from '@/components/Dialog/Dialog.tsx'
import { IconButton } from '@/components/IconButton/IconButton.tsx'
import { Menu } from '@/components/Menu/Menu.tsx'
import { MenuItem } from '@/components/Menu/MenuItem.tsx'
import { MenuSection } from '@/components/Menu/MenuSection.tsx'
import { Select } from '@/components/Select/Select.tsx'
import { SelectItem } from '@/components/Select/SelectItem.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import { toastQueue } from '@/lib/toastQueue.ts'
import styles from './DesignSystem.module.css'

export function OverlaysSection() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [appearance, setAppearance] = useState('system')
  return (
    <Section
      title="Overlays"
      intro="Selects, menus, a dialog and toasts. Open each one: hover an option for the overlay, use the arrow keys, and press Escape to close."
    >
      <div className={styles.samples}>
        <Sample label="Select: with a placeholder, as an unset outcome, and with a value, as the plan switcher">
          <Select label="Outcome" placeholder="Choose an outcome">
            <SelectItem id="pass">Pass</SelectItem>
            <SelectItem id="fail">Fail</SelectItem>
          </Select>
          <Select label="Plan" defaultSelectedKey="a">
            <SelectItem id="a" description="ABC1001F, ABC1002F">
              Alpha and Beta
            </SelectItem>
            <SelectItem id="b" description="ABC1001F, ABC1003F">
              Alpha and Gamma
            </SelectItem>
          </Select>
        </Sample>
        <Sample label="Menus: the account menu, with a choice and a destructive action, and chat history, with icons">
          <Menu label="Account" trigger={<Button variant="secondary">Account</Button>}>
            <MenuSection
              title="Appearance"
              selectionMode="single"
              selectedKeys={[appearance]}
              onSelectionChange={(keys) => {
                const [key] = keys // one choice, so never 'all'
                setAppearance(String(key))
              }}
            >
              <MenuItem id="system">Match System</MenuItem>
              <MenuItem id="light">Light</MenuItem>
              <MenuItem id="dark">Dark</MenuItem>
            </MenuSection>
            <MenuItem id="sign-out" isDestructive>
              Sign Out
            </MenuItem>
          </Menu>
          <Menu label="Chat History" trigger={<IconButton label="Chat History" icon="history" />}>
            <MenuSection title="Chats in This View">
              <MenuItem id="chat-1" icon="chat_bubble">
                Can I swap an elective?
              </MenuItem>
              <MenuItem id="chat-2" icon="chat_bubble">
                Is this plan clash-free?
              </MenuItem>
            </MenuSection>
          </Menu>
        </Sample>
        <Sample label="Dialog">
          <Button variant="secondary" onPress={() => setDialogOpen(true)}>
            Open Dialog
          </Button>
          <Dialog title="Add a Course" isOpen={dialogOpen} onOpenChange={setDialogOpen}>
            <p>Escape, the close button and a click outside all close this dialog. Focus stays inside it while it is open.</p>
            <Button onPress={() => setDialogOpen(false)}>Done</Button>
          </Dialog>
        </Sample>
        <Sample label="Toasts: close after 5 seconds, unless hovered or focused">
          <Button
            variant="secondary"
            onPress={() => toastQueue.add({ title: 'Saved', description: 'Your answers are kept.' }, { timeout: 5000 })}
          >
            Show Toast
          </Button>
          <Button
            variant="secondary"
            onPress={() =>
              toastQueue.add(
                { title: 'Could not save', action: { label: 'Retry', onPress: () => undefined } },
                { timeout: 5000 },
              )
            }
          >
            Show Toast with Action
          </Button>
        </Sample>
      </div>
    </Section>
  )
}
