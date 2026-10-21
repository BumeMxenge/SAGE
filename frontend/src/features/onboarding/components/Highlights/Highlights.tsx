// Three things SAGE does, side by side on a strip that slides one highlight into view at a time, on
// React Aria's Tabs. A dot, the arrow keys, or a swipe, a drag or a sideways trackpad scroll anywhere on
// the highlights moves it, never a timer, so nothing needs pausing. Each dot is a tab named after its highlight, with a hit
// area of at least 24 px. Each picture is one image to a screen reader, named by what it shows.
import { type ReactNode, useCallback, useState } from 'react'
import { Tab, TabList, TabPanel, Tabs } from 'react-aria-components'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './Highlights.module.css'
import { useSwipe } from './useSwipe.ts'

const highlights: { id: string; title: string; shows: string; picture: ReactNode }[] = [
  {
    id: 'timetables',
    title: 'Timetables That Work in Practice, Not Just on Paper',
    shows:
      "STA2020F's practical, Wednesday 14:00 to 16:00, clashes with CSC1015F's lecture, Wednesday 15:00 to 16:00. SAGE finds the two slots that work: STA2020F on Tuesday at 09:00 and CSC1015F on Wednesday at 15:00.",
    picture: (
      <>
        <div className={styles.clash}>
          <p className={`${styles.block} ${styles.orange}`}>
            <strong>STA2020F practical</strong> Wed 14:00 – 16:00
          </p>
          <p className={`${styles.block} ${styles.pink}`}>
            <strong>CSC1015F lecture</strong> Wed 15:00 – 16:00
          </p>
        </div>
        <p className={styles.finds}>
          <span className={styles.arrow}>
            <Icon name="arrow_downward" />
          </span>
          SAGE finds the two slots that work
        </p>
        <div className={`${styles.card} ${styles.slots}`}>
          <p className={`${styles.block} ${styles.teal}`}>
            <strong>STA2020F</strong> Tue 09:00
          </p>
          <p className={`${styles.block} ${styles.darkTeal}`}>
            <strong>CSC1015F</strong> Wed 15:00
          </p>
        </div>
      </>
    ),
  },
  {
    id: 'answers',
    title: 'Instant Answers, Grounded in the EBE Handbook',
    shows:
      'A student asks whether they can take STA2020F after failing MAM1000W last year. SAGE answers not yet, as STA2020F lists MAM1000W as a prerequisite, gives two routes, repeating MAM1000W this year or applying for a prerequisite concession, and cites page 148 of the Engineering & the Built Environment Handbook 2026.',
    picture: (
      <>
        <p className={styles.question}>Can I take STA2020F if I failed MAM1000W last year?</p>
        <div className={`${styles.card} ${styles.answer}`}>
          <p>Not yet. STA2020F lists MAM1000W as a prerequisite, so registration will be blocked until it's passed.</p>
          <p className={styles.routes}>
            Two routes: repeat MAM1000W this year, or apply for a prerequisite concession through your faculty office.
          </p>
          <p className={styles.source}>Engineering & the Built Environment Handbook 2026, p.148</p>
        </div>
      </>
    ),
  },
  {
    id: 'credits',
    title: 'Course Lists That Sit Inside Your Credit Limits',
    shows:
      "Year 4 of Mechatronics in the 2026 handbook: the five core courses make 90 credits, and two 16-credit electives, EEE4119F and EEE4118F, bring the year to 122. One more 16-credit elective makes 138, the year's minimum, with the 48 elective credits it asks for.",
    picture: (
      <>
        <div className={`${styles.card} ${styles.load}`}>
          <p className={styles.loadTitle}>
            <strong>Credit load, Year 4</strong>
            <span className={styles.total}>122 / 138</span>
          </p>
          <p className={styles.limits}>
            <span>Electives min 48</span>
            <span>Total min 138</span>
          </p>
          <p className={styles.bar}>
            <span className={styles.navy} />
            <span className={styles.teal} />
            <span className={styles.darkTeal} />
            <span className={styles.room} />
          </p>
          <ul className={styles.legend}>
            <li>
              <span className={`${styles.swatch} ${styles.navy}`} />
              Core courses <span className={styles.credits}>90</span>
            </li>
            <li>
              <span className={`${styles.swatch} ${styles.teal}`} />
              EEE4119F <span className={styles.credits}>16</span>
            </li>
            <li>
              <span className={`${styles.swatch} ${styles.darkTeal}`} />
              EEE4118F <span className={styles.credits}>16</span>
            </li>
            <li className={styles.free}>
              <span className={`${styles.swatch} ${styles.room}`} />
              Room for one 16-credit elective
            </li>
          </ul>
        </div>
        <p className={`${styles.card} ${styles.verdict}`}>
          <span className={styles.tick} />
          One more 16-credit elective makes 138, with 48 in electives.
        </p>
      </>
    ),
  },
]

export function Highlights() {
  const [{ shown, round }, setView] = useState({ shown: 0, round: false })
  // Round and round: on from the last highlight is the first, and back from the first is the last.
  // Going round slides the strip past every highlight, so it takes longer, as in the prototype.
  const step = useCallback((by: 1 | -1) => {
    setView((view) => {
      const next = view.shown + by
      return { shown: (next + highlights.length) % highlights.length, round: next < 0 || next >= highlights.length }
    })
  }, [])
  const swipe = useSwipe(step)
  return (
    <Tabs
      ref={swipe}
      selectedKey={highlights[shown].id}
      onSelectionChange={(key) => {
        // A dot or an arrow key takes the usual time, however far it goes, as the prototype's dots do
        setView({ shown: highlights.findIndex(({ id }) => id === key), round: false })
      }}
      className={styles.highlights}
    >
      {/* The dots come first, as the panels take their ids from them; CSS shows them underneath */}
      <TabList aria-label="Highlights" className={styles.dots}>
        {highlights.map(({ id, title }) => (
          <Tab key={id} id={id} aria-label={title} className={styles.dot} />
        ))}
      </TabList>
      <div className={styles.window}>
        {/* Every highlight stays on the strip, each on a slide as wide as the sand panel, so those out
            of view sit wholly outside it, and React Aria makes them inert */}
        <div className={styles.strip} data-round={round || undefined} style={{ '--shown': shown }}>
          {highlights.map(({ id, title, shows, picture }) => (
            <div key={id} className={styles.slide}>
              <TabPanel id={id} shouldForceMount className={styles.panel}>
                <h2 className={styles.title}>{title}</h2>
                {/* An img element can't hold an HTML drawing, so the role makes this one image instead */}
                {/* oxlint-disable-next-line jsx-a11y/prefer-tag-over-role */}
                <div role="img" aria-label={shows}>
                  <div aria-hidden="true" className={styles.drawing}>
                    {picture}
                  </div>
                </div>
              </TabPanel>
            </div>
          ))}
        </div>
      </div>
    </Tabs>
  )
}
