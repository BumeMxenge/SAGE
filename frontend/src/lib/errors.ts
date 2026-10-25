// What a student reads when a request fails: a title, a message and an action for every problem code
// the API sends, and for the three ways a request fails before the API can answer. The satisfies
// below makes the build fail when a code has no entry. The words come from each refusal's meaning in
// backend/src/sage/shared/errors.py and from the error sheet's copy, by the design audit's rules:
// Title Case titles, sentence-case messages, and SAGE in capitals.
import { ApiError, type ErrorCode } from './api.ts'

// What gets the student past an error. The screen that shows it builds its own button from the name.
type ErrorAction = 'retry' | 'go_to_plan'

// Each action's button, so every screen names the same action the same way
export const actionLabels: Record<ErrorAction, string> = {
  retry: 'Try Again',
  go_to_plan: 'Go to My Plan',
}

type Entry = {
  title: string
  // A function where the words name what the refusal carries, such as both student numbers
  message: string | ((error: ApiError) => string)
  // The button a screen offers to get past the error, if any, such as Try Again
  action: ErrorAction | null
}

const entries = {
  not_found: {
    title: 'Something Is Missing',
    message: "SAGE couldn't find what this page asked for. Go back to your plan and try again.",
    action: 'go_to_plan',
  },
  method_not_allowed: {
    title: 'Something Went Wrong',
    message: "This page asked SAGE for something it can't do. Go back to your plan and try again.",
    action: 'go_to_plan',
  },
  invalid_request: {
    title: 'Some Details Need Fixing',
    message: "Part of what you sent isn't valid. Check the marked fields and try again.",
    action: null,
  },
  internal_error: {
    title: 'Something Went Wrong',
    message: 'SAGE ran into a problem. Try again, and if it keeps happening, quote the reference.',
    action: 'retry',
  },
  not_signed_in: {
    title: 'Your Session Has Expired',
    message: 'Sign in again to carry on.',
    action: null,
  },
  uct_account_required: {
    title: "This Account Can't Use SAGE",
    message: 'SAGE is for UCT students. Sign in with your student account, the one ending in @myuct.ac.za.',
    action: null,
  },
  students_only: {
    title: "Staff Tools Aren't Built Yet",
    message: "This part of SAGE is for students. Tools for staff aren't part of this version.",
    action: null,
  },
  rulebook_not_loaded: {
    title: "SAGE Isn't Ready Yet",
    message: "The handbook rules aren't loaded yet. Try again in a few minutes.",
    action: 'retry',
  },
  unknown_curriculum: {
    title: "That Programme Isn't Available",
    message: "It isn't in this year's handbook. Choose the programme you're registered on.",
    action: null,
  },
  unknown_result: {
    title: "A Result Isn't Recognised",
    message: "One of the outcomes isn't a UCT result symbol. Check them and try again.",
    action: null,
  },
  not_a_pdf: {
    title: "That File Isn't a PDF",
    message: 'Export your transcript as a PDF and upload it again.',
    action: null,
  },
  file_too_large: {
    title: 'That File Is Too Large',
    message: 'Your transcript must be 10 MB or less. Upload a smaller PDF.',
    action: null,
  },
  transcript_unreadable: {
    title: "SAGE Couldn't Read This Transcript",
    message: 'Download it again from PeopleSoft and upload the new copy.',
    action: null,
  },
  not_a_transcript: {
    title: "This Isn't a UCT Academic Record",
    message: 'Upload the academic record you downloaded from PeopleSoft.',
    action: null,
  },
  transcript_not_yours: {
    title: 'This Transcript Belongs to Another Student',
    message: ({ problem }) =>
      `This transcript is for ${problem?.transcript_student_number}, but you're signed in as ${problem?.account_student_number}.`,
    action: null,
  },
  transcript_incomplete: {
    title: 'This Transcript Is Missing Pages',
    message: 'Download your whole academic record from PeopleSoft again and upload it.',
    action: null,
  },
  no_course_history: {
    title: 'Your Record Has No Courses Yet',
    message:
      "SAGE plans from your course history, so there's nothing to plan from yet. First-year registration follows the fixed first-year curriculum in the handbook.",
    action: null,
  },
  onboarding_incomplete: {
    title: 'Finish Setting Up First',
    message: 'Upload your transcript and confirm your course history, then try again.',
    action: null,
  },
  plans_not_ready: {
    title: "Your Plans Aren't Ready Yet",
    message: 'SAGE is still preparing your plans. Try again in a moment.',
    action: 'retry',
  },
  plan_not_found: {
    title: "This Plan Doesn't Exist",
    message: 'It may have been replaced, or the link belongs to another account.',
    action: 'go_to_plan',
  },
  same_plan: {
    title: 'Choose Two Different Plans',
    message: "A plan can't be compared with itself.",
    action: null,
  },
  questionnaire_not_needed: {
    title: 'No Questions Needed',
    message: 'You have few enough plans to choose from without them.',
    action: 'go_to_plan',
  },
  questionnaire_answered: {
    title: "You've Already Answered",
    message: 'Your answers are saved, and your plans are ready.',
    action: 'go_to_plan',
  },
  unknown_answer: {
    title: "That Answer Isn't an Option",
    message: 'Choose one of the answers shown.',
    action: null,
  },
  no_plan_matches: {
    title: 'No Plan Fits All Your Answers',
    message: 'Change one answer and try again.',
    action: null,
  },
  course_not_found: {
    title: "That Course Isn't in the Handbook",
    message: "It isn't in this year's handbook, so it can't be added.",
    action: null,
  },
  course_doesnt_fit: {
    title: "That Course Doesn't Fit This Plan",
    message: "It isn't one of the courses that fit this plan's timetable.",
    action: null,
  },
  different_plan_sets: {
    title: "These Plans Can't Share a Chat",
    message: 'One of these plans has been replaced. Choose two plans from your current list.',
    action: null,
  },
  questionnaire_pending: {
    title: 'Answer the Questions First',
    message: 'Answer the questionnaire before you chat about your plans.',
    action: 'go_to_plan',
  },
  chat_not_found: {
    title: "This Chat Doesn't Exist",
    message: 'It may belong to another account. Start a new chat instead.',
    action: null,
  },
  advisor_unavailable: {
    title: "The Assistant Couldn't Reply",
    message: "Your question wasn't saved. Try again in a moment.",
    action: 'retry',
  },
  network_error: {
    title: "Can't Reach SAGE",
    message: 'Check your internet connection, then try again.',
    action: 'retry',
  },
  timeout: {
    title: 'SAGE Is Taking Too Long',
    message: "SAGE didn't answer in time. Try again.",
    action: 'retry',
  },
  server_unavailable: {
    title: "SAGE Isn't Responding",
    message: 'SAGE is unavailable right now. Try again in a minute.',
    action: 'retry',
  },
} satisfies Record<ErrorCode, Entry>

type Explanation = {
  title: string
  message: string
  action: ErrorAction | null
  reference: string | undefined // a server error's, for support to trace it
}

// The words for any error a screen catches. One that isn't an ApiError, such as a page whose code
// failed to load, gets a server error's words.
export function explain(error: unknown): Explanation {
  if (!(error instanceof ApiError)) return { ...entries.internal_error, reference: undefined }
  const { title, message, action } = entries[error.code]
  return {
    title,
    message: typeof message === 'string' ? message : message(error),
    action,
    reference: error.problem?.reference ?? undefined,
  }
}
