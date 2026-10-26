// The plan view's words for a plan's credits, its complementary slots and their previews

// A plan's credits, and any its slots leave to choose, such as "138 credits + 18 to choose"
export const creditsOf = (total: number, toChoose: number) =>
  toChoose > 0 ? `${total} credits + ${toChoose} to choose` : `${total} credits`

export const slotTitle = 'Complementary Studies'

// While previewing a course: "138 credits + 15 with Word Power", and any credits still to choose
export const creditsWith = (total: number, credits: number, name: string, toChoose: number) =>
  `${total} credits + ${credits} with ${name}${toChoose > 0 ? ` + ${toChoose} to choose` : ''}`

export const previewingLine = (name: string) => `Previewing ${name} in this plan. Nothing is saved.`

export const endPreview = 'End Preview'

export const previewCourse = (name: string) => `Preview ${name}`

// What a screen reader hears while a preview is on its way
export const loadingPreview = 'Loading the preview…'

// The mark beside a preview's course in the course list
export const previewMark = 'Preview'

// What a screen reader hears while her favourites are on their way
export const loadingFavourites = 'Loading your favourites…'

// A favourite offered in two terms that fit, named by its term
export const previewCourseIn = (name: string, term: string) => `Preview ${name}, ${term}`

// What a screen reader hears after a preview's course in the week
export const inThisPreview = 'in this preview'

// A block of the plan's own course whose section a preview fixes, such as "Lab A, fixed by this preview"
export const fixedByPreview = (options: string) => `${options}, fixed by this preview`

// A 576-credit place, named after the course it takes the place of
export const inPlaceOf = (code: string) => `In Place of ${code}`

// "an" before a number said with a vowel sound: 8, 11, 18 and the eighties, which covers any credits
const article = (credits: number) => (credits === 8 || credits === 11 || credits === 18 || (credits >= 80 && credits < 90) ? 'an' : 'a')

export const lineNeeds = (credits: number) => `Add ${article(credits)} ${credits}-credit complementary studies course.`

export const placeNeeds = (credits: number) => `An approved complementary course of at least ${credits} credits.`

// How many courses fit, and how many of those need her advisor to check them
export function fitting(fits: number, checks: number): string {
  const courses = fits === 1 ? '1 course fits this plan' : `${fits} courses fit this plan`
  if (checks === 0) return `${courses}.`
  if (fits === 1) return `${courses}, and it needs a check with your advisor.`
  return `${courses}, ${checks} of them ${checks === 1 ? 'needs' : 'need'} a check with your advisor.`
}

export const browse = (fits: number) => (fits === 1 ? 'Browse the Course That Fits' : `Browse the ${fits} That Fit`)
