// The review's working copy of the transcript: the lines the student keeps and the programme they are
// on. It lives only in the page's memory, and nothing is saved until Finish Setup sends setupOf(...)
// in one request.
import type { components } from '@/lib/api-types.ts'

type Transcript = components['schemas']['Transcript']
type Setup = components['schemas']['Setup']

// A line on screen, with a key of its own for the table
export type ReviewLine = components['schemas']['TranscriptLine'] & { id: string }

type Review = { lines: ReviewLine[]; curriculum: string | null }

export function startReview(transcript: Transcript): Review {
  return {
    lines: transcript.lines.map((line, index) => ({ ...line, id: `read-${index}` })),
    // A transcript that names one programme decides it; otherwise the student chooses
    curriculum: transcript.curriculum_options.length === 1 ? transcript.curriculum_options[0].code : null,
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
