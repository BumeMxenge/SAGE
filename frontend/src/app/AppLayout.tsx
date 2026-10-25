// The frame around the student's pages: the sidebar, and beside it the page, which React Router swaps
// as the address changes while the sidebar stays as it is. The sidebar is the page's banner, holding
// the logo, the main navigation (audit §5) and the account. It folds to a rail of icons and opens
// again. Folded, the labels stay in the page, clipped from view, so each link keeps its name, and a
// tooltip shows it beside the icon instead. At a plan's own address the assistant sits on the page's
// other side, outside its main landmark, as the named aside approved difference 6 asks for.
import { useEffect, useState } from 'react'
import { Button, Link } from 'react-aria-components'
import { Outlet, useLocation, useParams } from 'react-router'
import { IconButton } from '@/components/actions/IconButton/IconButton.tsx'
import { Icon, type PlainIconName } from '@/components/brand/Icon/Icon.tsx'
import { Logo } from '@/components/brand/Logo/Logo.tsx'
import { Tooltip } from '@/components/overlays/Tooltip/Tooltip.tsx'
import { AssistantRail } from '@/features/assistant/AssistantRail.tsx'
import type { View } from '@/features/plan/components/TermView/TermView.tsx'
import { nav } from '@/lib/copy.ts'
import { AccountMenu } from './AccountMenu.tsx'
import styles from './AppLayout.module.css'

const pages: { href: string; label: string; icon: PlainIconName }[] = [
  { href: '/plan', label: nav.plan, icon: 'calendar_today' },
  { href: '/electives', label: nav.electives, icon: 'explore' },
  { href: '/history', label: nav.history, icon: 'schedule' },
]

// What the frame tells the page beside the sidebar: whether the sidebar and the assistant are both
// open, leaving a plan so little room that its controls show only their icons, as the prototype's do,
// and the plan's view, Calendar or Course List. The frame keeps the view, as it keeps the assistant
// open or folded, so one chosen while her plan loads, at /plan or before the guard has decided on the
// first load, stays when the plan opens, and as she moves between pages.
export type PageRoom = { iconOnly: boolean; view: View; onViewChange: (view: View) => void }

// Narrower windows start with the sidebar folded, as the prototype does, which also keeps a page usable
// at 400% zoom (WCAG 1.4.10). Read inside the component, as the route table's tests load this file in
// Node, which has no window.
const wideWindow = '(min-width: 1100px)'

export function AppLayout() {
  const { pathname } = useLocation()
  // Only a plan's own address names one
  const { planId } = useParams()
  const [collapsed, setCollapsed] = useState(() => !window.matchMedia(wideWindow).matches)
  // The assistant starts folded, as the prototype's does, and stays as she leaves it while she moves
  // between pages
  const [assistantOpen, setAssistantOpen] = useState(false)
  const [view, setView] = useState<View>('calendar')
  // A pressed toggle disappears as the sidebar changes shape, so the one that replaces it takes focus.
  // Only a press sets this: the window's width, or the account menu opening the sidebar, moves no focus.
  const [moveFocus, setMoveFocus] = useState(false)

  // Narrowing the window past the width folds the sidebar, and widening it opens it again
  useEffect(() => {
    const wide = window.matchMedia(wideWindow)
    const follow = () => {
      setCollapsed(!wide.matches)
      setMoveFocus(false)
    }
    wide.addEventListener('change', follow)
    return () => wide.removeEventListener('change', follow)
  }, [])

  function toggle() {
    setCollapsed(!collapsed)
    setMoveFocus(true)
  }

  function openForMenu() {
    setCollapsed(false)
    setMoveFocus(false)
  }

  // A plan's own address, /plan/:planId, is still the Plan page
  const isCurrent = (href: string) => pathname === href || pathname.startsWith(`${href}/`)

  return (
    <div className={styles.frame}>
      <header className={styles.sidebar} data-collapsed={collapsed || undefined}>
        <div className={styles.top}>
          {collapsed ? (
            <Tooltip text="Open Sidebar" placement="end">
              <Button
                aria-label="Open Sidebar"
                // Only after a toggle press, never as a page opens: see moveFocus
                // oxlint-disable-next-line jsx-a11y/no-autofocus
                autoFocus={moveFocus}
                onPress={toggle}
                className={styles.open}
              >
                <span className={styles.mark}>
                  <Logo variant="mark" />
                </span>
                <span className={styles.openIcon}>
                  <Icon name="dock_to_right" />
                </span>
              </Button>
            </Tooltip>
          ) : (
            <>
              <Logo variant="compact" small />
              <IconButton
                label="Collapse Sidebar"
                icon="dock_to_right"
                // Only after a toggle press, never as a page opens: see moveFocus
                // oxlint-disable-next-line jsx-a11y/no-autofocus
                autoFocus={moveFocus}
                onPress={toggle}
              />
            </>
          )}
        </div>
        <nav aria-label="Main" className={styles.nav}>
          {pages.map(({ href, label, icon }) => (
            <Tooltip key={href} text={label} placement="end" isDisabled={!collapsed}>
              <Link href={href} aria-current={isCurrent(href) ? 'page' : undefined} className={styles.link}>
                <Icon name={icon} />
                {label}
              </Link>
            </Tooltip>
          ))}
        </nav>
        <AccountMenu collapsed={collapsed} onOpen={openForMenu} />
      </header>
      <main className={styles.main}>
        <Outlet context={{ iconOnly: !collapsed && assistantOpen, view, onViewChange: setView } satisfies PageRoom} />
      </main>
      {planId && <AssistantRail open={assistantOpen} onOpenChange={setAssistantOpen} />}
    </div>
  )
}
