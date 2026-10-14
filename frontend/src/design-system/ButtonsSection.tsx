import { useState } from 'react'
import { Button } from '@/components/Button/Button.tsx'
import { IconButton } from '@/components/IconButton/IconButton.tsx'
import { Logo } from '@/components/Logo/Logo.tsx'
import { Segment } from '@/components/SegmentedControl/Segment.tsx'
import { SegmentedControl } from '@/components/SegmentedControl/SegmentedControl.tsx'
import { ToggleButton } from '@/components/ToggleButton/ToggleButton.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

export function ButtonsSection() {
  const [term, setTerm] = useState('sem-1')
  return (
    <Section
      title="Buttons"
      intro="Hover and focus are live: hover a button, then press Tab to see the focus ring. Primary fades slightly, secondary turns teal, quiet and icon buttons get a soft overlay. A pending button shows a spinner and announces Loading."
    >
      <div className={styles.samples}>
        <Sample label="Primary: rest, disabled, pending">
          <Button>Create Registration Plan</Button>
          <Button isDisabled>Continue</Button>
          <Button isPending>Show My Plans</Button>
        </Sample>
        <Sample label="Secondary: rest, disabled, pending">
          <Button variant="secondary">Compare</Button>
          <Button variant="secondary" isDisabled>
            Compare
          </Button>
          <Button variant="secondary" isPending>
            Compare
          </Button>
        </Sample>
        <Sample label="Quiet: rest, disabled">
          <Button variant="quiet">Back</Button>
          <Button variant="quiet" isDisabled>
            Back
          </Button>
        </Sample>
        <Sample label="Sign-in: rest">
          <div className={styles.narrow}>
            <Button variant="sign-in">
              <Logo variant="microsoft" />
              Continue with UCT Email
            </Button>
          </div>
        </Sample>
        <Sample label="Icon button: rest, disabled. Hover or focus for the tooltip">
          <IconButton label="Collapse Panel" icon="left_panel_close" />
          <IconButton label="Open Assistant" icon="chat_bubble" isDisabled />
        </Sample>
        <Sample label="Favourite toggle: off, on, disabled">
          <ToggleButton label="Favourite ABC1001F" />
          <ToggleButton label="Favourite ABC1002F" defaultSelected />
          <ToggleButton label="Favourite ABC1003F" isDisabled />
        </Sample>
        <Sample label="Segmented control: one chosen, and disabled">
          <SegmentedControl label="Term" selectedKey={term} onChange={setTerm}>
            <Segment id="sem-1">Sem 1</Segment>
            <Segment id="sem-2">Sem 2</Segment>
            <Segment id="winter">Winter</Segment>
            <Segment id="summer">Summer</Segment>
          </SegmentedControl>
          <SegmentedControl label="View" selectedKey="calendar" onChange={setTerm} isDisabled>
            <Segment id="calendar">Calendar</Segment>
            <Segment id="list">Course List</Segment>
          </SegmentedControl>
        </Sample>
      </div>
    </Section>
  )
}
