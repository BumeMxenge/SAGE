// The account at the foot of the sidebar: who is signed in, and a menu to choose the appearance or to
// sign out. SAGE keeps no names: the name is the one this browser read from Microsoft at sign-in, and
// with none the student number stands in, beside a person icon (approved difference 14). The API has no
// programme or year, so the student number and the UCT email take the prototype's second lines.
import { useQuery } from '@tanstack/react-query'
import { Button } from 'react-aria-components'
import { useNavigate } from 'react-router'
import { Account } from '@/components/content/Account/Account.tsx'
import { Menu } from '@/components/overlays/Menu/Menu.tsx'
import { MenuItem } from '@/components/overlays/Menu/MenuItem.tsx'
import { MenuSection } from '@/components/overlays/Menu/MenuSection.tsx'
import { Tooltip } from '@/components/overlays/Tooltip/Tooltip.tsx'
import { useAuth } from '@/lib/auth/useAuth.ts'
import { appearanceOptions } from '@/lib/copy.ts'
import { queries } from '@/lib/queryKeys.ts'
import { type Appearance, useAppearance } from '@/lib/useAppearance.ts'
import styles from './AccountMenu.module.css'

const appearances = Object.keys(appearanceOptions) as Appearance[]

type AccountMenuProps = { collapsed: boolean; onOpen: () => void }

export function AccountMenu({ collapsed, onOpen }: AccountMenuProps) {
  const { name, loading, signOut } = useAuth()
  // Already in the cache, as the guard read it before the page opened. Not the suspense version: Sign
  // Out empties the cache while this is still on screen, and that version would throw to the error page.
  const { data: me } = useQuery(queries.me())
  const { appearance, choose } = useAppearance()
  const navigate = useNavigate()

  // Nothing shows until the name is known, so a student number never turns into a name
  if (loading || !me) return null

  const number = me.student_number ?? me.email
  const person = name
    ? { title: `${name.givenName} ${name.surname}`, detail: number, initials: name.givenName.charAt(0) + name.surname.charAt(0) }
    : { title: number, detail: me.email, initials: undefined }

  async function signOutAndLeave() {
    await signOut()
    // Replacing the address, so Back can't return to a page that would only send them away
    await navigate('/sign-in', { replace: true })
  }

  return (
    <div className={styles.account} data-collapsed={collapsed || undefined}>
      <Menu
        label="Account"
        header={<Account initials={person.initials} name={person.title} detail={me.email} />}
        onOpenChange={(isOpen) => {
          if (isOpen) onOpen()
        }}
        trigger={
          <Tooltip text={person.title} placement="end" isDisabled={!collapsed}>
            <Button className={styles.button}>
              <Account initials={person.initials} name={person.title} detail={person.detail} />
            </Button>
          </Tooltip>
        }
      >
        {/* Each choice acts on its own press; the section only shows which is chosen */}
        <MenuSection title="Appearance" selectionMode="single" selectedKeys={[appearance]}>
          {appearances.map((option) => (
            <MenuItem key={option} id={option} onAction={() => choose(option)}>
              {appearanceOptions[option]}
            </MenuItem>
          ))}
        </MenuSection>
        <MenuItem id="sign-out" isDestructive onAction={() => void signOutAndLeave()}>
          Sign Out
        </MenuItem>
      </Menu>
    </div>
  )
}
