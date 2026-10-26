// The account at the foot of the sidebar: who is signed in, and a menu to choose the appearance or to
// sign out. SAGE keeps no names: the name is the one this browser read from Microsoft at sign-in, and
// with none the student number stands in, beside a person icon (approved difference 14). The API has no
// programme or year, so the student number and the UCT email take the prototype's second lines. Until
// the account and the name are known, a skeleton holds the button's place, so a student number never
// turns into a name.
import { useQuery } from '@tanstack/react-query'
import { Button } from 'react-aria-components'
import { useNavigate } from 'react-router'
import { Account } from '@/components/content/Account/Account.tsx'
import { AccountSkeleton } from '@/components/content/Account/AccountSkeleton.tsx'
import { Arrival } from '@/components/feedback/Arrival/Arrival.tsx'
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
  // The guard's read, in the cache once it has decided, and on its way while the first load waits for
  // it. The account only watches it, so the first load's frame asks nothing of its own before the
  // guard decides.
  const read = useQuery({ ...queries.me(), enabled: false })
  const { appearance, choose } = useAppearance()
  const navigate = useNavigate()

  // To /sign-in, replacing the address, so Back can't return to a page that would only send them away.
  // flushSync draws the move at once rather than as a transition, so her pages have closed before
  // signOut empties the cache, and none of them shows its skeleton or asks for its reads again.
  const signOutAndLeave = () => signOut(() => navigate('/sign-in', { replace: true, flushSync: true }))

  return (
    <div className={styles.account} data-collapsed={collapsed || undefined}>
      <Arrival
        data={loading ? undefined : read.data}
        waiting={loading || read.isPending}
        skeleton={
          <span className={styles.waiting}>
            <AccountSkeleton />
          </span>
        }
        status="Loading your account…"
      >
        {(me) => {
          const number = me.student_number ?? me.email
          const person = name
            ? { title: `${name.givenName} ${name.surname}`, detail: number, initials: name.givenName.charAt(0) + name.surname.charAt(0) }
            : { title: number, detail: me.email, initials: undefined }
          return (
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
          )
        }}
      </Arrival>
    </div>
  )
}
