// The course picker: a dialog to find a catalogue course for one year, by its code or name, and pick
// it to add. The list is Select's own OptionList, so it looks and works like every other list of
// options: Tab reaches it, the arrow keys move through it, and Enter picks.
import { useState } from 'react'
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import { SearchField } from '@/components/inputs/SearchField/SearchField.tsx'
import { OptionList } from '@/components/inputs/Select/OptionList.tsx'
import { SelectItem } from '@/components/inputs/Select/SelectItem.tsx'
import { Dialog } from '@/components/overlays/Dialog/Dialog.tsx'
import type { components } from '@/lib/api-types.ts'
import styles from './CoursePicker.module.css'

type Course = components['schemas']['Course']

type CoursePickerProps = {
  year: number
  // The catalogue's courses the year doesn't have yet
  courses: Course[]
  onClose: () => void
  onPick: (course: Course) => void
}

export function CoursePicker({ year, courses, onClose, onPick }: CoursePickerProps) {
  const [search, setSearch] = useState('')
  const query = search.trim().toLowerCase()
  const matches = courses.filter((course) => `${course.code} ${course.name}`.toLowerCase().includes(query))
  const byCode = new Map(matches.map((course) => [course.code, course]))
  return (
    <Dialog
      title="Add a Course"
      isOpen
      onOpenChange={(isOpen) => {
        if (!isOpen) onClose()
      }}
    >
      <div className={styles.picker}>
        <p className={styles.lead}>Pick a course to add to {year}.</p>
        <SearchField label="Search courses" placeholder="Search by course name or code" value={search} onChange={setSearch} />
        {matches.length > 0 ? (
          <OptionList aria-label={`Courses to add to ${year}`} onAction={(code) => onPick(byCode.get(String(code))!)}>
            {matches.map((course) => (
              <SelectItem key={course.code} id={course.code} description={course.name} detail={`${course.credits} credits`}>
                {course.code}
              </SelectItem>
            ))}
          </OptionList>
        ) : (
          <EmptyState title="No Matching Courses" message="Try another course name or code." />
        )}
      </div>
    </Dialog>
  )
}
