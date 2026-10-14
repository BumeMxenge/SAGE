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
  const [view, setView] = useState('calendar')
  return (
    <Section
      title="Buttons"
      intro="Hover and focus are live: hover a button, then press Tab to see the focus ring. Primary fades slightly, secondary turns teal, quiet and icon buttons get a soft overlay, and the sign-in button darkens."
    >
      <div className={styles.samples}>
        <Sample label="Primary: rest, and disabled as Continue is before a transcript is read">
          <Button>Create Registration Plan</Button>
          <Button isDisabled>Continue</Button>
        </Sample>
        <Sample label="Secondary">
          <Button variant="secondary">Compare</Button>
        </Sample>
        <Sample label="Quiet">
          <Button variant="quiet">Back</Button>
        </Sample>
        <Sample label="Icon buttons. Hover or focus for the tooltip">
          <IconButton label="Collapse Panel" icon="dock_to_right" />
          <IconButton label="New Chat" icon="border_color" />
          <IconButton label="Chat History" icon="history" />
        </Sample>
        <Sample label="Favourite: off and on">
          <ToggleButton label="Favourite ABC1001F" />
          <ToggleButton label="Favourite ABC1002F" defaultSelected />
        </Sample>
      </div>
      <div className={styles.wide}>
        <Sample label="Sign-in: as long as the sign-in form, light only">
          <Button variant="sign-in">
            <Logo variant="microsoft" />
            Continue with UCT Email
          </Button>
        </Sample>
      </div>
      <div className={styles.samples}>
        <Sample label="Segmented control: the terms">
          <SegmentedControl label="Term" selectedKey={term} onChange={setTerm}>
            <Segment id="sem-1">Sem 1</Segment>
            <Segment id="sem-2">Sem 2</Segment>
            <Segment id="winter">Winter</Segment>
            <Segment id="summer">Summer</Segment>
          </SegmentedControl>
        </Sample>
        <Sample label="The view, in words">
          <SegmentedControl label="View" selectedKey={view} onChange={setView}>
            <Segment id="calendar">Calendar</Segment>
            <Segment id="list">Course List</Segment>
          </SegmentedControl>
        </Sample>
        <Sample label="The view as icons, when the sidebar and the assistant are both open">
          <SegmentedControl label="View" selectedKey={view} onChange={setView}>
            <Segment id="calendar" icon="calendar_today">
              Calendar
            </Segment>
            <Segment id="list" icon="format_list_bulleted">
              Course List
            </Segment>
          </SegmentedControl>
        </Sample>
      </div>
    </Section>
  )
}
