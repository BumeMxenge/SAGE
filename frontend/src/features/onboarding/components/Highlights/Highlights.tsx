// Three things SAGE does, one at a time, on React Aria's Tabs. Each dot is a tab named after its
// highlight, with a hit area of at least 24 px, and the arrow keys move between them. Only a click or
// a key changes the highlight, never a timer, so nothing needs pausing. Each picture is one image to a
// screen reader, named by what it shows.
import type { ReactNode } from 'react'
import { Tab, TabList, TabPanel, Tabs } from 'react-aria-components'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './Highlights.module.css'

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
      "Semester 1's credit load: STA2020F, CSC1015F and MAM1000W at 14 credits each make 42, between the minimum of 36 and the maximum of 48, with room for one 6-credit elective. 42 credits is inside the limits, so no concession is needed.",
    picture: (
      <>
        <div className={`${styles.card} ${styles.load}`}>
          <p className={styles.loadTitle}>
            <strong>Credit load, Semester 1</strong>
            <span className={styles.total}>42 / 48</span>
          </p>
          <p className={styles.limits}>
            <span>Min 36</span>
            <span>Max 48</span>
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
              STA2020F <span className={styles.credits}>14</span>
            </li>
            <li>
              <span className={`${styles.swatch} ${styles.teal}`} />
              CSC1015F <span className={styles.credits}>14</span>
            </li>
            <li>
              <span className={`${styles.swatch} ${styles.darkTeal}`} />
              MAM1000W <span className={styles.credits}>14</span>
            </li>
            <li className={styles.free}>
              <span className={`${styles.swatch} ${styles.room}`} />
              Room for one 6-credit elective
            </li>
          </ul>
        </div>
        <p className={`${styles.card} ${styles.verdict}`}>
          <span className={styles.tick} />
          42 credits: inside the limits, no concession needed.
        </p>
      </>
    ),
  },
]

export function Highlights() {
  return (
    <Tabs className={styles.highlights}>
      {/* The dots come first, as the panels take their ids from them; CSS shows them underneath */}
      <TabList aria-label="Highlights" className={styles.dots}>
        {highlights.map(({ id, title }) => (
          <Tab key={id} id={id} aria-label={title} className={styles.dot} />
        ))}
      </TabList>
      {highlights.map(({ id, title, shows, picture }) => (
        <TabPanel key={id} id={id} className={styles.panel}>
          <h2 className={styles.title}>{title}</h2>
          {/* An img element can't hold an HTML drawing, so the role makes this one image instead */}
          {/* oxlint-disable-next-line jsx-a11y/prefer-tag-over-role */}
          <div role="img" aria-label={shows}>
            <div aria-hidden="true" className={styles.drawing}>
              {picture}
            </div>
          </div>
        </TabPanel>
      ))}
    </Tabs>
  )
}
