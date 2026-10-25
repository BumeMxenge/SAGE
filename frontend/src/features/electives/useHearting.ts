// A card's one heart, through the heart routes: hearting sends PUT for each offering she can heart,
// and unhearting DELETE for each she hearted. The card changes as she presses it. If any write fails,
// those that saved are undone, so both offerings change or neither, and the card is put back, with a
// toast saying so and Try Again (error case 12). After any failure the electives are read again, so
// the card shows what's saved even if an undo failed too.
import { useMutation } from '@tanstack/react-query'
import { client, dataOf } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import { actionLabels } from '@/lib/errors.ts'
import { queryClient } from '@/lib/queryClient.ts'
import { queries, refresh } from '@/lib/queryKeys.ts'
import { toastQueue } from '@/lib/toastQueue.ts'
import { withHeart } from './cards.ts'
import { heartFailed } from './copy.ts'

type Elective = components['schemas']['Elective']
type Change = { card: Elective; heart: boolean }

const electives = queries.electives().queryKey

function write(code: string, heart: boolean) {
  const path = { params: { path: { course_code: code } } }
  return dataOf(heart ? client.PUT('/v1/favourites/{course_code}', path) : client.DELETE('/v1/favourites/{course_code}', path))
}

export function useHearting() {
  const hearting = useMutation({
    mutationFn: async ({ card, heart }: Change) => {
      const codes = card.offerings.filter((offering) => (heart ? offering.can_heart : offering.hearted)).map((offering) => offering.code)
      const written = await Promise.allSettled(codes.map((code) => write(code, heart)))
      const failed = written.find((result) => result.status === 'rejected')
      if (!failed) return
      await Promise.allSettled(codes.filter((_, at) => written[at].status === 'fulfilled').map((code) => write(code, !heart)))
      throw failed.reason
    },
    onMutate: async ({ card, heart }) => {
      // A read still on its way would land over the heart she just pressed
      await queryClient.cancelQueries({ queryKey: electives })
      const before = queryClient.getQueryData(electives)
      queryClient.setQueryData(electives, (data) => data && withHeart(data, card, heart))
      return { before }
    },
    onError: async (_error, change, context) => {
      queryClient.setQueryData(electives, context?.before)
      // A toast, as she has moved on and nothing waits on it. The error sheet keeps it 6 seconds.
      toastQueue.add({ title: heartFailed, action: { label: actionLabels.retry, onPress: () => hearting.mutate(change) } }, { timeout: 6000 })
      await refresh.favouriteChanged()
    },
    onSuccess: () => refresh.favouriteChanged(),
  })
  return hearting
}
