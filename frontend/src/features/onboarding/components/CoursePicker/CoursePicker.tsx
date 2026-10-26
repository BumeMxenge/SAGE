// The course picker: a dialog to find a catalogue course for one year, by its code or name, and pick
// it to add. Programme courses and complementary studies sit on two sides, as the prototype's Core and
// Electives do, programme courses first each time it opens, and the search looks within the side
// shown. The list is Select's own OptionList, so it looks and works like every other list of options:
// Tab reaches it, the arrow keys move through it, and Enter picks.
import { useState } from 'react'
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import { SearchField } from '@/components/inputs/SearchField/SearchField.tsx'
import { Segment } from '@/components/inputs/SegmentedControl/Segment.tsx'
import { SegmentedControl } from '@/components/inputs/SegmentedControl/SegmentedControl.tsx'
import { OptionList } from '@/components/inputs/Select/OptionList.tsx'
import { SelectItem } from '@/components/inputs/Select/SelectItem.tsx'
import { Dialog } from '@/components/overlays/Dialog/Dialog.tsx'
import type { components } from '@/lib/api-types.ts'
import styles from './CoursePicker.module.css'

type Course = components['schemas']['CatalogueCourse']

// Each side, and the other side's name, for the hint when nothing on this one matches
const sides = {
  programme: { name: 'Programme Courses', other: 'Complementary Studies' },
  complementary: { name: 'Complementary Studies', other: 'Programme Courses' },
}
type Side = keyof typeof sides
const isSide = (key: string): key is Side => Object.hasOwn(sides, key)

type CoursePickerProps = {
  year: number
  // The catalogue's courses the year doesn't have yet
  courses: Course[]
  onClose: () => void
  onPick: (course: Course) => void
}

export function CoursePicker({ year, courses, onClose, onPick }: CoursePickerProps) {
  const [search, setSearch] = useState('')
  const [side, setSide] = useState<Side>('programme')
  const query = search.trim().toLowerCase()
  const matches = courses.filter(
    (course) =>
      course.complementary === (side === 'complementary') && `${course.code} ${course.name}`.toLowerCase().includes(query),
  )
  const byCode = new Map(matches.map((course) => [course.code, course]))
  return (
    <Dialog title="Add a Course" onClose={onClose}>
      <div className={styles.picker}>
        <p className={styles.lead}>Pick a course to add to {year}.</p>
        <SearchField label="Search courses" placeholder="Search by course name or code" value={search} onChange={setSearch} />
        <SegmentedControl
          label="Course type"
          selectedKey={side}
          onChange={(key) => {
            if (isSide(key)) setSide(key)
          }}
          fill
        >
          <Segment id="programme">{sides.programme.name}</Segment>
          <Segment id="complementary">{sides.complementary.name}</Segment>
        </SegmentedControl>
        {/* The results keep one height, so the dialog stays one size whether courses match or not */}
        <div className={styles.results}>
          {matches.length > 0 ? (
            <OptionList aria-label={`Courses to add to ${year}`} onAction={(code) => onPick(byCode.get(String(code))!)}>
              {matches.map((course) => (
                <SelectItem key={course.code} id={course.code} description={course.name} detail={`${course.credits} credits`}>
                  {course.code}
                </SelectItem>
              ))}
            </OptionList>
          ) : (
            <EmptyState
              title="No Matching Courses"
              message={`Try another course name or code, or look in ${sides[side].other}.`}
            />
          )}
        </div>
      </div>
    </Dialog>
  )
}
