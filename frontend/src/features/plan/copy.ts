// The plan view's words for a plan's credits and its complementary slots

// A plan's credits, and any its slots leave to choose, such as "138 credits + 18 to choose"
export const creditsOf = (total: number, toChoose: number) =>
  toChoose > 0 ? `${total} credits + ${toChoose} to choose` : `${total} credits`

export const slotTitle = 'Complementary Studies'

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
