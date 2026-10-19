// Finish Setup sends exactly the lines the student kept, as they left them: a removed line is absent, a
// changed outcome is sent, and an added course carries the catalogue's name, credits and term, with
// no NQF level or mark. The record is made up, and the expected request is written out by hand.
import { expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { type ReviewAction, reviewReducer, setupOf, startReview } from './review.ts'

const transcript: components['schemas']['Transcript'] = {
  student_number: 'QRTILV999',
  programme: 'Made-up Programme',
  curriculum_options: [{ code: 'MADE01', name: 'Made-up Programme 4-year curriculum' }],
  issued_on: null,
  warnings: [],
  lines: [
    {
      academic_year: 2024,
      term: 'sem1',
      course_code: 'EEE2045F',
      course_name: 'Analogue Electronics',
      credits: 16,
      nqf_level: 6,
      result: '2-',
      mark: 63,
      unverified: false,
    },
    {
      academic_year: 2024,
      term: 'sem2',
      course_code: 'EEE2047S',
      course_name: 'Signals and Systems I',
      credits: 16,
      nqf_level: 6,
      result: 'SP',
      mark: 50,
      unverified: true,
    },
    {
      academic_year: 2025,
      term: 'sem1',
      course_code: 'EEE3088F',
      course_name: 'Design Principles',
      credits: 16,
      nqf_level: 7,
      result: 'OS',
      mark: null,
      unverified: false,
    },
  ],
}

it('sends exactly the lines the student kept, as they left them', () => {
  const start = startReview(transcript)
  const [analogue, , design] = start.lines
  const edits: ReviewAction[] = [
    { type: 'remove', id: analogue.id },
    { type: 'changeOutcome', id: design.id, result: '2+' },
    {
      type: 'add',
      year: 2024,
      course: { code: 'EEE2044S', name: 'Introduction to Power Engineering', credits: 16, term: 'sem2' },
      result: 'PA',
    },
  ]
  const edited = edits.reduce(reviewReducer, start)

  expect(setupOf('MADE01', edited.lines)).toEqual({
    curriculum_code: 'MADE01',
    lines: [
      // Kept as read, without the review's own fields
      {
        academic_year: 2024,
        term: 'sem2',
        course_code: 'EEE2047S',
        course_name: 'Signals and Systems I',
        credits: 16,
        nqf_level: 6,
        result: 'SP',
        mark: 50,
      },
      // With the outcome the student chose
      {
        academic_year: 2025,
        term: 'sem1',
        course_code: 'EEE3088F',
        course_name: 'Design Principles',
        credits: 16,
        nqf_level: 7,
        result: '2+',
        mark: null,
      },
      // Added, as the catalogue has it
      {
        academic_year: 2024,
        term: 'sem2',
        course_code: 'EEE2044S',
        course_name: 'Introduction to Power Engineering',
        credits: 16,
        nqf_level: null,
        result: 'PA',
        mark: null,
      },
    ],
  })
})
