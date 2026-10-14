import { useState } from 'react'
import { Button } from '@/components/Button/Button.tsx'
import { Dialog } from '@/components/Dialog/Dialog.tsx'
import { Menu } from '@/components/Menu/Menu.tsx'
import { MenuItem } from '@/components/Menu/MenuItem.tsx'
import { MenuSection } from '@/components/Menu/MenuSection.tsx'
import { Select } from '@/components/Select/Select.tsx'
import { SelectItem } from '@/components/Select/SelectItem.tsx'
import { SelectSection } from '@/components/Select/SelectSection.tsx'
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
        <Sample label="Select: with a placeholder, with a value, grouped, disabled, error">
          <Select label="Plan" placeholder="Choose a plan">
            <SelectItem id="a" description="ABC1001F, ABC1002F">
              Alpha and Beta
            </SelectItem>
            <SelectItem id="b" description="ABC1001F, ABC1003F">
              Alpha and Gamma
            </SelectItem>
          </Select>
          <Select label="Plan" defaultSelectedKey="a">
            <SelectSection title="Shown">
              <SelectItem id="a" description="ABC1001F, ABC1002F">
                Alpha and Beta
              </SelectItem>
            </SelectSection>
            <SelectSection title="Hidden by Your Answers">
              <SelectItem id="b" description="ABC1001F, ABC1003F">
                Alpha and Gamma
              </SelectItem>
            </SelectSection>
          </Select>
          <Select label="Plan" isDisabled placeholder="Choose a plan">
            <SelectItem id="a">Alpha and Beta</SelectItem>
          </Select>
          <Select label="Plan" isInvalid errorMessage="Choose a plan to go on" placeholder="Choose a plan">
            <SelectItem id="a">Alpha and Beta</SelectItem>
          </Select>
        </Sample>
        <Sample label="Menu: a choice with a tick, and a destructive action">
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
              <MenuItem id="system" icon="contrast">
                Match System
              </MenuItem>
              <MenuItem id="light" icon="light_mode">
                Light
              </MenuItem>
              <MenuItem id="dark" icon="dark_mode">
                Dark
              </MenuItem>
            </MenuSection>
            <MenuItem id="sign-out" icon="logout" isDestructive>
              Sign Out
            </MenuItem>
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
