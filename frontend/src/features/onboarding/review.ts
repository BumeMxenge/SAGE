// The review's working copy of the transcript: the lines the student keeps, changes or adds, and the
// programme they are on. It lives only in the page's memory, and nothing is saved until Finish Setup
// sends setupOf(...) in one request.
import type { components } from '@/lib/api-types.ts'

type Transcript = components['schemas']['Transcript']
type Course = components['schemas']['Course']
type Setup = components['schemas']['Setup']

// A line on screen, with a key of its own for the table
export type ReviewLine = components['schemas']['TranscriptLine'] & { id: string }

type Review = { lines: ReviewLine[]; curriculum: string | null }

export type ReviewAction =
  | { type: 'chooseCurriculum'; code: string }
  | { type: 'remove'; id: string }
  | { type: 'changeOutcome'; id: string; result: string }
  | { type: 'add'; year: number; course: Course; result: string }

export function startReview(transcript: Transcript): Review {
  return {
    lines: transcript.lines.map((line, index) => ({ ...line, id: `read-${index}` })),
    // A transcript that names one programme decides it; otherwise the student chooses
    curriculum: transcript.curriculum_options.length === 1 ? transcript.curriculum_options[0].code : null,
  }
}

export function reviewReducer(review: Review, action: ReviewAction): Review {
  switch (action.type) {
    case 'chooseCurriculum':
      return { ...review, curriculum: action.code }
    case 'remove':
      return { ...review, lines: review.lines.filter((line) => line.id !== action.id) }
    case 'changeOutcome':
      return {
        ...review,
        lines: review.lines.map((line) => (line.id === action.id ? { ...line, result: action.result } : line)),
      }
    case 'add': {
      const { year, course, result } = action
      // An added course is the catalogue's: its code, name, credits and term. Nothing printed its NQF
      // level or a mark, so it has neither, and none of it was guessed.
      const line: ReviewLine = {
        id: `added-${year}-${course.code}`,
        academic_year: year,
        term: course.term,
        course_code: course.code,
        course_name: course.name,
        credits: course.credits,
        nqf_level: null,
        result,
        mark: null,
        unverified: false,
      }
      return { ...review, lines: [...review.lines, line] }
    }
  }
}

// What Finish Setup sends: the programme, and each kept line without the review's own fields
export function setupOf(curriculum: string, lines: ReviewLine[]): Setup {
  return {
    curriculum_code: curriculum,
    lines: lines.map(({ academic_year, term, course_code, course_name, credits, nqf_level, result, mark }) => ({
      academic_year,
      term,
      course_code,
      course_name,
      credits,
      nqf_level,
      result,
      mark,
    })),
  }
}
