// The review's working copy of the transcript: the lines the student keeps, changes or adds, and the
// programme they are on. It lives only in the page's memory, and nothing is saved until Finish Setup
// sends setupOf(...) in one request.
import type { components } from '@/lib/api-types.ts'

type Transcript = components['schemas']['Transcript']
type Course = components['schemas']['Course']
type Setup = components['schemas']['Setup']
export type Outcome = components['schemas']['ResultSymbol']['outcome']

// The seven outcomes the review shows, in the order its lists give them, each with the result symbol
// a line the student changes or adds is saved with. SAGE's checks read a line's outcome, never its
// class of pass, so each is UCT's plain symbol for its outcome (public.result_symbols): PA, a pass
// with no class, as on a pass-or-fail course; F, a fail; OS, a result not yet available; FS, a fail
// with a supplementary exam allowed; DPR, a duly performed certificate refused; CR, a credit; and
// EXC, a credit excluded. Such a line has no mark.
export const outcomes: Record<Outcome, { word: string; symbol: string }> = {
  pass: { word: 'Passed', symbol: 'PA' },
  fail: { word: 'Failed', symbol: 'F' },
  in_progress: { word: 'In progress', symbol: 'OS' },
  supp_pending: { word: 'Supplementary pending', symbol: 'FS' },
  dp_refused: { word: 'DP refused', symbol: 'DPR' },
  credited: { word: 'Credited', symbol: 'CR' },
  not_counted: { word: 'Not counted', symbol: 'EXC' },
}

// Whether a list's key is an outcome, as every list of outcomes keys its options by outcome
export function isOutcome(key: unknown): key is Outcome {
  return typeof key === 'string' && Object.hasOwn(outcomes, key)
}

// The word for a result symbol's outcome, or the symbol itself where the catalogue doesn't know it
export function wordFor(result: string, outcomeOf: Map<string, Outcome>): string {
  const outcome = outcomeOf.get(result)
  return outcome ? outcomes[outcome].word : result
}

// A line on screen, with a key of its own for the table
export type ReviewLine = components['schemas']['TranscriptLine'] & { id: string }

type Review = { lines: ReviewLine[]; curriculum: string | null }

export type ReviewAction =
  | { type: 'chooseCurriculum'; code: string }
  | { type: 'remove'; id: string }
  | { type: 'changeOutcome'; id: string; outcome: Outcome }
  | { type: 'add'; year: number; course: Course; outcome: Outcome }

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
    // The printed mark went with the printed result, so a changed outcome has none
    case 'changeOutcome':
      return {
        ...review,
        lines: review.lines.map((line) =>
          line.id === action.id ? { ...line, result: outcomes[action.outcome].symbol, mark: null } : line,
        ),
      }
    case 'add': {
      const { year, course, outcome } = action
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
        result: outcomes[outcome].symbol,
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
