// A plan's week in one term, worked out with no markup and no sizes: the meetings the week draws, the
// hours it spans, each course's colour, the line naming what has no set time, and in a preview, the
// course it adds and the sections it fixes. A block's place is in minutes from the week's first hour
// and its lane among meetings at the same time; the stylesheet turns those into a position against
// the hour's height. Which tab each term falls under is the address's (lib/planAddress.ts).
import type { components } from '@/lib/api-types.ts'
import { termLabels } from '@/lib/copy.ts'
import { inTerm, type PlanTerm, planTerms } from '@/lib/planAddress.ts'
import { fixedByPreview } from './copy.ts'

type Plan = components['schemas']['Plan']
type PlanCourse = components['schemas']['PlanCourse']
type Meeting = components['schemas']['Meeting']
type TermCode = Meeting['term']
type ForcedSection = components['schemas']['ForcedSection']

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
  previewed: boolean // a meeting of the course a preview adds
}

// A preview's course, and the sections of the plan's own courses it fixes
export type PreviewMarks = { code: string; forced: ForcedSection[] }

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
  fixed: string | null // the section a preview fixes it to
}

// What a block says of its sections: the one a preview fixes, "Lab A, fixed by this preview", or the
// alternatives left
function optionsOfDraft({ kind, choices, fixed }: Pick<Draft, 'kind' | 'choices' | 'fixed'>): string | null {
  if (fixed) return fixedByPreview(optionsOf(kind, [fixed]))
  return choices.length > 0 ? optionsOf(kind, choices) : null
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
    const { begins, ends, kind, choices, fixed, ...rest } = draft
    const block: Block = {
      ...rest,
      start: begins - firstHour * 60,
      length: ends - begins,
      options: optionsOfDraft({ kind, choices, fixed }),
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

// A course's choice groups that still leave alternatives to choose between. The API lists only the
// alternatives that fit the plan, so a group with one left is fixed.
function openGroupsOf(course: PlanCourse): Set<string> {
  const choices = new Map<string, Set<string>>()
  for (const { choice_group: group, choice } of course.meetings) {
    if (group && choice) choices.set(group, (choices.get(group) ?? new Set()).add(choice))
  }
  return new Set([...choices].filter(([, each]) => each.size > 1).map(([group]) => group))
}

// The shortest week drawn, 08:00 to 17:00, and the week a plan's skeleton draws while it's on its way
export const shortestWeek = { firstHour: 8, hours: 9 }

// A plan's week in one term. It runs from 08:00 to 17:00, or further to fit its meetings. A course's
// alternatives at the same day and time are one block naming them all, rather than lanes of their own,
// and the meetings of a group with one alternative left draw as any other. In a preview, the course it
// adds is marked, and so is each section of the plan's own courses it fixes.
export function weekOf(plan: Plan, tab: PlanTerm, preview?: PreviewMarks): Week {
  const drafts = new Map<string, Draft>()
  for (const course of plan.courses) {
    const open = openGroupsOf(course)
    const fixes = preview?.forced.filter((section) => section.course_code === course.code) ?? []
    course.meetings.forEach((meeting, index) => {
      if (!inTerm(meeting.term, tab) || !isTimed(meeting)) return
      const begins = minutesOf(meeting.start_time)
      const ends = minutesOf(meeting.end_time)
      const group = meeting.choice_group !== null && open.has(meeting.choice_group) ? meeting.choice_group : null
      const choice = group ? meeting.choice : null
      const key = group ? `${course.code}/${group}/${meeting.day}/${begins}/${ends}` : `${course.code}/${index}`
      const merged = drafts.get(key)
      if (merged && choice) {
        if (!merged.choices.includes(choice)) merged.choices.push(choice)
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
        choices: choice ? [choice] : [],
        quarter: quarterOf(meeting.term),
        previewed: course.code === preview?.code,
        fixed: fixes.find((section) => section.choice_group === meeting.choice_group && section.choice === meeting.choice)?.choice ?? null,
      })
    })
  }
  const all = [...drafts.values()]
  const firstHour = Math.min(shortestWeek.firstHour, ...all.map((draft) => Math.floor(draft.begins / 60)))
  const lastHour = Math.max(shortestWeek.firstHour + shortestWeek.hours, ...all.map((draft) => Math.ceil(draft.ends / 60)))
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

// A week's blocks row by row: the hour, then the day
const rowByRow = ({ blocks }: Week) =>
  [...blocks].sort((a, b) => Math.floor(a.start / 60) - Math.floor(b.start / 60) || a.day - b.day || a.start - b.start)

// Each course's one colour across a set of plans, so it never changes between plans or in compare.
// Term by term, the plans are read in the order given, each week row by row, and a course met for the
// first time takes the first colour no other course of that term has. A course coloured in an earlier
// term, such as a full-year course, keeps its colour, so no course of the later term takes it. Once a
// term has all eight, they start again at teal.
export function coloursOf(plans: Plan[]): Map<string, CourseColour> {
  const colours = new Map<string, CourseColour>()
  for (const term of planTerms) {
    const met = new Set(plans.flatMap((plan) => rowByRow(weekOf(plan, term)).map(({ code }) => code)))
    const taken = new Set([...met].flatMap((code) => colours.get(code) ?? []))
    let again = 0
    for (const code of met) {
      if (colours.has(code)) continue
      const colour = courseColours.find((each) => !taken.has(each)) ?? courseColours[again++ % courseColours.length]
      colours.set(code, colour)
      taken.add(colour)
    }
  }
  return colours
}
