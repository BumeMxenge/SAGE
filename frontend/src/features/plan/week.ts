// A plan's week in one term, worked out with no markup and no sizes: which tab each term falls under,
// the meetings the week draws, the hours it spans, each course's colour, and the line naming what has
// no set time. A block's place is in minutes from the week's first hour and its lane among meetings at
// the same time; the stylesheet turns those into a position against the hour's height.
import type { components } from '@/lib/api-types.ts'
import { termLabels } from '@/lib/copy.ts'
import type { PlanTerm } from '@/lib/planAddress.ts'

type Plan = components['schemas']['Plan']
type PlanCourse = components['schemas']['PlanCourse']
type Meeting = components['schemas']['Meeting']
type TermCode = Meeting['term']

// The tabs a term shows under: a quarter inside its semester, a full-year course in both semesters,
// and practical training's "other" in none
const tabsOf: Record<TermCode, readonly PlanTerm[]> = {
  q1: ['sem1'],
  q2: ['sem1'],
  sem1: ['sem1'],
  q3: ['sem2'],
  q4: ['sem2'],
  sem2: ['sem2'],
  full_year: ['sem1', 'sem2'],
  winter: ['winter'],
  summer: ['summer'],
  other: [],
}

export const inTerm = (term: TermCode, tab: PlanTerm) => tabsOf[term].includes(tab)

// The mark beside a course that runs for one quarter of its semester, such as Q3
export function quarterOf(term: TermCode): string | null {
  return term === 'q1' || term === 'q2' || term === 'q3' || term === 'q4' ? termLabels[term] : null
}

// The courses a term's list shows
export const termCourses = (plan: Plan, tab: PlanTerm) => plan.courses.filter((course) => inTerm(course.term, tab))

// "A", "A or B", "A, B or C"
function listOf(items: string[], conjunction: 'and' | 'or'): string {
  return items.length > 1 ? `${items.slice(0, -1).join(', ')} ${conjunction} ${items.at(-1)}` : items.join('')
}

type TimedMeeting = Meeting & { day: number; start_time: string; end_time: string }

const isTimed = (meeting: Meeting): meeting is TimedMeeting =>
  meeting.day !== null && meeting.start_time !== null && meeting.end_time !== null

// The API's "14:00:00" in minutes after midnight, and back to "14:00"
const minutesOf = (time: string) => Number(time.slice(0, 2)) * 60 + Number(time.slice(3, 5))
const clockOf = (time: string) => time.slice(0, 5)

// The words for alternatives the plan hasn't chosen between, from the meeting's kind and its choices as
// the API gives them, never a letter worked out here: "Lab A", or for choices of more than one word,
// "Practical: Monday and Wednesday or Monday and Thursday"
function optionsOf(kind: string, choices: string[]): string {
  const named = `${kind.charAt(0).toUpperCase()}${kind.slice(1)}`
  const listed = listOf(choices, 'or')
  return choices.some((choice) => choice.includes(' ')) ? `${named}: ${listed}` : `${named} ${listed}`
}

export type Block = {
  key: string // unique in its week
  code: string
  name: string
  day: number // 1 is Monday
  start: number // minutes after the week's first hour
  length: number // in minutes
  from: string // its clock times, such as 14:00
  to: string
  options: string | null // the alternatives it stands for, such as "Lab A"
  quarter: string | null
  lane: number // its place among the meetings it overlaps, from 0
  lanes: number // how many lanes those meetings take
}

export type Week = {
  firstHour: number
  hours: number
  blocks: Block[] // by day, then start
  noSetTimes: string | null
}

type Draft = Omit<Block, 'start' | 'length' | 'options' | 'lane' | 'lanes'> & {
  begins: number // minutes after midnight
  ends: number
  kind: string
  choices: string[]
}

// One day's meetings in lanes. Each takes the first lane free when it starts, so meetings that only
// touch, one ending as the next starts, share a lane. A run of meetings that overlap, one into the
// next, takes as many lanes as meet at once.
function inLanes(day: Draft[], firstHour: number): Block[] {
  const blocks: Block[] = []
  let run: Block[] = []
  let laneEnds: number[] = [] // when each lane of the run is free again
  const closeRun = () => {
    for (const block of run) block.lanes = laneEnds.length
  }
  for (const draft of [...day].sort((a, b) => a.begins - b.begins || a.ends - b.ends)) {
    if (run.length > 0 && draft.begins >= Math.max(...laneEnds)) {
      closeRun()
      run = []
      laneEnds = []
    }
    const free = laneEnds.findIndex((end) => end <= draft.begins)
    const lane = free === -1 ? laneEnds.length : free
    laneEnds[lane] = draft.ends
    const { begins, ends, kind, choices, ...rest } = draft
    const block: Block = {
      ...rest,
      start: begins - firstHour * 60,
      length: ends - begins,
      options: choices.length > 0 ? optionsOf(kind, choices) : null,
      lane,
      lanes: 1,
    }
    run.push(block)
    blocks.push(block)
  }
  closeRun()
  return blocks
}

// The line under the week for what it can't draw: the term's courses with no meetings in it, and
// meetings with no day or time, such as a practical by arrangement
function noSetTimesOf(courses: PlanCourse[], tab: PlanTerm): string | null {
  const unmet = courses.filter((course) => inTerm(course.term, tab) && !course.meetings.some((meeting) => inTerm(meeting.term, tab)))
  const arranged = new Set(
    courses.flatMap((course) =>
      course.meetings
        .filter((meeting) => inTerm(meeting.term, tab) && !isTimed(meeting))
        .map((meeting) => (meeting.kind ? `${course.code} ${meeting.kind}` : course.code)),
    ),
  )
  const parts = [
    ...(unmet.length > 0 ? [listOf(unmet.map((course) => `${course.code} ${course.name}`), 'and')] : []),
    ...[...arranged].map((what) => `${what}: by arrangement`),
  ]
  return parts.length > 0 ? `No set times this term: ${parts.join('. ')}.` : null
}

// A plan's week in one term. It runs from 08:00 to 17:00, or further to fit its meetings. A course's
// alternatives at the same day and time are one block naming them all, rather than lanes of their own.
export function weekOf(plan: Plan, tab: PlanTerm): Week {
  const drafts = new Map<string, Draft>()
  for (const course of plan.courses) {
    course.meetings.forEach((meeting, index) => {
      if (!inTerm(meeting.term, tab) || !isTimed(meeting)) return
      const begins = minutesOf(meeting.start_time)
      const ends = minutesOf(meeting.end_time)
      const group = meeting.choice_group
      const key = group ? `${course.code}/${group}/${meeting.day}/${begins}/${ends}` : `${course.code}/${index}`
      const merged = drafts.get(key)
      if (merged && meeting.choice) {
        if (!merged.choices.includes(meeting.choice)) merged.choices.push(meeting.choice)
        return
      }
      drafts.set(key, {
        key,
        code: course.code,
        name: course.name,
        day: meeting.day,
        begins,
        ends,
        from: clockOf(meeting.start_time),
        to: clockOf(meeting.end_time),
        kind: meeting.kind ?? group ?? 'option',
        choices: meeting.choice ? [meeting.choice] : [],
        quarter: quarterOf(meeting.term),
      })
    })
  }
  const all = [...drafts.values()]
  const firstHour = Math.min(8, ...all.map((draft) => Math.floor(draft.begins / 60)))
  const lastHour = Math.max(17, ...all.map((draft) => Math.ceil(draft.ends / 60)))
  const days = [...new Set(all.map((draft) => draft.day))].sort((a, b) => a - b)
  return {
    firstHour,
    hours: lastHour - firstHour,
    blocks: days.flatMap((day) =>
      inLanes(
        all.filter((draft) => draft.day === day),
        firstHour,
      ).sort((a, b) => a.start - b.start || a.lane - b.lane),
    ),
    noSetTimes: noSetTimesOf(plan.courses, tab),
  }
}

// The timetable's eight course colours, in the order it gives them out. The stylesheet maps each to
// its --color-course-* token.
export const courseColours = ['teal', 'orange', 'navy', 'pink', 'blue', 'ochre', 'purple', 'dark-teal'] as const
export type CourseColour = (typeof courseColours)[number]

// Each course's colour, given out in the order courses first appear, reading each week row by row:
// the hour, then the day. After the eighth they start again at teal. Compare reads both plans' weeks,
// the open plan's first, so a course they share keeps one colour, and the open plan keeps its own.
export function coloursOf(weeks: Week[]): Map<string, CourseColour> {
  const colours = new Map<string, CourseColour>()
  for (const { blocks } of weeks) {
    const rowByRow = [...blocks].sort((a, b) => Math.floor(a.start / 60) - Math.floor(b.start / 60) || a.day - b.day || a.start - b.start)
    for (const { code } of rowByRow) {
      if (!colours.has(code)) colours.set(code, courseColours[colours.size % courseColours.length])
    }
  }
  return colours
}
