// A plan's week, on made-up plans and on Power, Control & Robotics' real meetings from the approved
// 2026 rulebook. Each expected value is worked out by hand in its comment, or comes from the prototype.
import { describe, expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { coloursOf, termCourses, weekOf } from './week.ts'

type Plan = components['schemas']['Plan']
type PlanCourse = components['schemas']['PlanCourse']
type Meeting = components['schemas']['Meeting']
type TermCode = Meeting['term']

const MON = 1
const TUE = 2
const WED = 3
const THU = 4
const FRI = 5

function meeting(term: TermCode, day: number | null, from: string | null, to: string | null, more: Partial<Meeting> = {}): Meeting {
  return {
    term,
    day,
    start_time: from === null ? null : `${from}:00`,
    end_time: to === null ? null : `${to}:00`,
    kind: null,
    choice_group: null,
    choice: null,
    ...more,
  }
}

function course(code: string, name: string, term: TermCode, meetings: Meeting[]): PlanCourse {
  return { code, name, credits: 16, term, groups: [], meetings }
}

function plan(courses: PlanCourse[]): Plan {
  return {
    id: 'p1',
    period: 2026,
    position: 1,
    name: 'A made-up plan',
    combination: null,
    hidden: false,
    credits: { total: 0, by_term: {} },
    courses,
    reasons: [],
  }
}

// One course a day at the given times, each its own made-up code
function day(...times: [string, string][]): Plan {
  return plan(times.map(([from, to], index) => course(`TST100${index}F`, 'Made up', 'sem1', [meeting('sem1', MON, from, to)])))
}

const lanes = (week: ReturnType<typeof weekOf>) => week.blocks.map(({ lane, lanes: of }) => [lane, of])

describe('meetings at the same time', () => {
  it('share the day only when they overlap: touching meetings keep the whole width', () => {
    // 10:45 is when the first ends and the second starts
    expect(lanes(weekOf(day(['10:00', '10:45'], ['10:45', '11:30']), 'sem1'))).toEqual([
      [0, 1],
      [0, 1],
    ])
    // A minute's overlap
    expect(lanes(weekOf(day(['10:00', '10:46'], ['10:45', '11:30']), 'sem1'))).toEqual([
      [0, 2],
      [1, 2],
    ])
  })

  it('take only as many lanes as meet at once, in a run where each overlaps the next', () => {
    // 09:00 to 10:00 overlaps 09:30 to 10:30, which overlaps 10:00 to 11:00, but the first and the
    // third only touch, so the third takes the first's lane: two lanes, not three
    expect(lanes(weekOf(day(['09:00', '10:00'], ['09:30', '10:30'], ['10:00', '11:00']), 'sem1'))).toEqual([
      [0, 2],
      [1, 2],
      [0, 2],
    ])
    // One that starts as the run's last meeting ends, at 10:30, overlaps none of it: the whole width
    expect(lanes(weekOf(day(['09:00', '10:00'], ['09:30', '10:30'], ['10:30', '11:00']), 'sem1'))).toEqual([
      [0, 2],
      [1, 2],
      [0, 1],
    ])
  })
})

describe('alternatives a plan leaves open', () => {
  // CSC3002F's practicals as the engine adds them: 14:00 to 18:00 on a pair of weekdays, each pair an
  // alternative, here the four pairs a made-up plan has room for
  const pairs = [
    ['Monday and Wednesday', MON, WED],
    ['Monday and Thursday', MON, THU],
    ['Monday and Friday', MON, FRI],
    ['Wednesday and Friday', WED, FRI],
  ] as const
  const practicals = pairs.flatMap(([choice, first, second]) =>
    [first, second].map((weekday) =>
      meeting('sem1', weekday, '14:00', '18:00', { kind: 'practical', choice_group: 'practical', choice }),
    ),
  )
  const networks = course('CSC3002F', 'Networks and Operating Systems', 'sem1', practicals)

  it("are one block for each day and time, naming every choice there as the API gives it", () => {
    const week = weekOf(plan([networks]), 'sem1')
    expect(week.blocks.map(({ day: weekday, options, lanes: of }) => [weekday, options, of])).toEqual([
      [MON, 'Practical: Monday and Wednesday, Monday and Thursday or Monday and Friday', 1],
      [WED, 'Practical: Monday and Wednesday or Wednesday and Friday', 1],
      [THU, 'Practical: Monday and Thursday', 1],
      [FRI, 'Practical: Monday and Friday or Wednesday and Friday', 1],
    ])
  })

  it('are named by their kind and their choice, with no letter assumed', () => {
    // EEE3096S's two labs and its lectures, from the approved 2026 rulebook
    const embedded = course('EEE3096S', 'Embedded Systems II', 'sem2', [
      meeting('sem2', TUE, '10:00', '11:45'),
      meeting('sem2', WED, '10:00', '11:45'),
      meeting('sem2', WED, '14:00', '17:45', { kind: 'lab', choice_group: 'lab', choice: 'B' }),
      meeting('sem2', FRI, '14:00', '17:45', { kind: 'lab', choice_group: 'lab', choice: 'A' }),
    ])
    expect(weekOf(plan([embedded]), 'sem2').blocks.map(({ day: weekday, from, options }) => [weekday, from, options])).toEqual([
      [TUE, '10:00', null],
      [WED, '10:00', null],
      [WED, '14:00', 'Lab B'],
      [FRI, '14:00', 'Lab A'],
    ])
  })

  it('draw as fixed meetings once one alternative is left in their group', () => {
    // The API lists only the alternatives that fit the plan: here EEE3096S's Lab A alone, and one
    // pair of CSC3002F's days
    const labA = course('EEE3096S', 'Embedded Systems II', 'sem2', [
      meeting('sem2', FRI, '14:00', '17:45', { kind: 'lab', choice_group: 'lab', choice: 'A' }),
    ])
    expect(weekOf(plan([labA]), 'sem2').blocks.map(({ day: weekday, options }) => [weekday, options])).toEqual([[FRI, null]])
    const onePair = course('CSC3002F', 'Networks and Operating Systems', 'sem1', [
      meeting('sem1', MON, '14:00', '18:00', { kind: 'practical', choice_group: 'practical', choice: 'Monday and Wednesday' }),
      meeting('sem1', WED, '14:00', '18:00', { kind: 'practical', choice_group: 'practical', choice: 'Monday and Wednesday' }),
    ])
    expect(weekOf(plan([onePair]), 'sem1').blocks.map(({ day: weekday, options }) => [weekday, options])).toEqual([
      [MON, null],
      [WED, null],
    ])
  })
})

describe('terms', () => {
  const quarter = course('EEE4125C', 'New Ventures', 'q3', [meeting('q3', TUE, '14:00', '15:45')])
  const fullYear = course('MUZ1339H', 'Jazz in Context I', 'full_year', [meeting('full_year', MON, '09:00', '09:45')])
  const winter = course('TST1000W', 'A winter course', 'winter', [meeting('winter', MON, '09:00', '09:45')])
  const year = plan([quarter, fullYear, winter])
  const codes = (tab: 'sem1' | 'sem2' | 'winter' | 'summer') => termCourses(year, tab).map(({ code }) => code)

  it('put a quarter in its semester, marked, a full-year course in both semesters, and a winter course in Winter alone', () => {
    expect(codes('sem1')).toEqual(['MUZ1339H'])
    expect(codes('sem2')).toEqual(['EEE4125C', 'MUZ1339H'])
    expect(codes('winter')).toEqual(['TST1000W'])
    expect(codes('summer')).toEqual([])
    expect(weekOf(year, 'sem2').blocks.map(({ code, quarter: mark }) => [code, mark])).toEqual([
      ['MUZ1339H', null],
      ['EEE4125C', 'Q3'],
    ])
  })
})

describe('the hours a week spans', () => {
  it('runs from 08:00 to 17:00, and to the next hour past a meeting that ends after 17:00', () => {
    expect(weekOf(plan([]), 'sem1')).toMatchObject({ firstHour: 8, hours: 9 })
    expect(weekOf(day(['16:00', '17:00']), 'sem1')).toMatchObject({ firstHour: 8, hours: 9 })
    // 17:01 needs the 17:00 hour, so the week ends at 18:00
    expect(weekOf(day(['16:00', '17:01']), 'sem1')).toMatchObject({ firstHour: 8, hours: 10 })
  })
})

// Power, Control & Robotics' and Power, Robotics & Imaging's Sem 1 meetings in the approved 2026
// rulebook
const law = course('CML4607F', 'Law for Engineers', 'sem1', [TUE, WED, THU, FRI].map((weekday) => meeting('sem1', weekday, '12:00', '12:45')))
const design = course('EEE4113F', 'Engineering System Design', 'sem1', [meeting('sem1', WED, '14:00', '15:45'), meeting('sem1', FRI, '14:00', '17:45')])
const energy = course('EEE4117F', 'Energy Conversion II', 'sem1', [
  meeting('sem1', MON, '08:00', '09:45'),
  meeting('sem1', WED, '08:00', '09:45'),
  meeting('sem1', FRI, '08:00', '08:45'),
])
const control = course('EEE4118F', 'Process Control and Instrumentation', 'sem1', [
  meeting('sem1', MON, '12:00', '12:45'),
  meeting('sem1', TUE, '10:00', '11:45'),
  meeting('sem1', THU, '10:00', '11:45'),
])
const mechatronics = course('EEE4119F', 'Mechatronics', 'sem1', [
  meeting('sem1', MON, '10:00', '11:45'),
  meeting('sem1', TUE, '08:00', '09:45'),
  meeting('sem1', WED, '10:00', '11:45'),
])
const imaging = course('HUB4049F', 'Introduction to Medical Imaging & Image Processing', 'sem1', [MON, TUE, WED].map((weekday) => meeting('sem1', weekday, '13:00', '14:00')))
const powerControlAndRobotics = plan([law, design, energy, control, mechatronics])
const powerRoboticsAndImaging = plan([law, design, energy, mechatronics, imaging])

describe('course colours', () => {
  it('go out in the order courses first appear, reading the week row by row', () => {
    // 08:00 row: EEE4117F on Monday, EEE4119F on Tuesday. 10:00: EEE4118F on Tuesday. 12:00: CML4607F
    // on Tuesday. 14:00: EEE4113F on Wednesday. The prototype gives these five the same colours.
    expect(Object.fromEntries(coloursOf([powerControlAndRobotics]))).toEqual({
      EEE4117F: 'teal',
      EEE4119F: 'orange',
      EEE4118F: 'navy',
      CML4607F: 'pink',
      EEE4113F: 'blue',
    })
    // Row by row, not day by day: Tuesday's 08:00 comes before Monday's 10:00
    const late = course('TST1002F', 'Made up', 'sem1', [meeting('sem1', MON, '10:00', '10:45')])
    const early = course('TST1001F', 'Made up', 'sem1', [meeting('sem1', TUE, '08:00', '08:45')])
    expect(Object.fromEntries(coloursOf([plan([late, early])]))).toEqual({ TST1001F: 'teal', TST1002F: 'orange' })
  })

  it('keep each course one colour across the set, a new course taking the first its term has free', () => {
    // Read alone, Power, Robotics & Imaging would give CML4607F navy, as the third course it meets.
    // Read after Power, Control & Robotics, CML4607F keeps pink and HUB4049F, new, takes the first
    // colour none of the five has, the sixth.
    const colours = coloursOf([powerControlAndRobotics, powerRoboticsAndImaging])
    expect(colours.get('CML4607F')).toBe('pink')
    expect(colours.get('HUB4049F')).toBe('ochre')
  })

  it("keep a full-year course's colour in both semesters, while each term otherwise starts afresh", () => {
    // Sem 1 meets the full-year course at 09:00, then TST1001F at 10:00: teal, orange. Sem 2 meets
    // TST2001S at 08:00 first. Teal is the full-year course's there too, and orange is free, as
    // TST1001F is in Sem 1 alone.
    const fullYear = course('TST1000H', 'Made up', 'full_year', [meeting('full_year', MON, '09:00', '09:45')])
    const first = course('TST1001F', 'Made up', 'sem1', [meeting('sem1', MON, '10:00', '10:45')])
    const second = course('TST2001S', 'Made up', 'sem2', [meeting('sem2', MON, '08:00', '08:45')])
    expect(Object.fromEntries(coloursOf([plan([fullYear, first, second])]))).toEqual({
      TST1000H: 'teal',
      TST1001F: 'orange',
      TST2001S: 'orange',
    })
  })

  it('start again at teal after the eighth', () => {
    // Nine courses, one an hour from 08:00
    const hours = Array.from({ length: 9 }, (_, index) => String(8 + index).padStart(2, '0'))
    const nine = day(...hours.map((hour): [string, string] => [`${hour}:00`, `${hour}:45`]))
    const colours = [...coloursOf([nine]).values()]
    expect(colours).toEqual(['teal', 'orange', 'navy', 'pink', 'blue', 'ochre', 'purple', 'dark-teal', 'teal'])
  })
})

describe('the line naming what has no set time', () => {
  const research = course('EEE4022S', 'Research Project', 'sem2', [])

  it('names the courses with no meetings, and each meeting with no day or time', () => {
    // CSC3024S as the engine gives it: a lecture every weekday at 10:00, and a practical by arrangement
    const cpp = course('CSC3024S', 'Introduction to C++ Programming', 'sem2', [
      ...[MON, TUE, WED, THU, FRI].map((weekday) => meeting('sem2', weekday, '10:00', '10:45', { kind: 'lecture' })),
      meeting('sem2', null, null, null, { kind: 'practical' }),
    ])
    expect(weekOf(plan([research, cpp]), 'sem2').noSetTimes).toBe(
      'No set times this term: EEE4022S Research Project. CSC3024S practical: by arrangement.',
    )
    // Mbali's second semester: two courses with no meetings, one of them a quarter's
    const impact = course('EEE4124C', 'Impact of Engineering on the Natural and Social Environment', 'q3', [])
    expect(weekOf(plan([research, impact]), 'sem2').noSetTimes).toBe(
      'No set times this term: EEE4022S Research Project and EEE4124C Impact of Engineering on the Natural and Social Environment.',
    )
  })

  it('is left out when everything in the term has a time', () => {
    expect(weekOf(powerControlAndRobotics, 'sem1').noSetTimes).toBeNull()
  })
})
