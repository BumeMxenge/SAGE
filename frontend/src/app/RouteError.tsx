// What shows when a page can't open: the guard couldn't reach SAGE, or the page's code failed to load
// or broke. It takes the whole page, with the error map's words and Try Again, which reloads it,
// as reloading is what gets past each of those.
import { useRouteError } from 'react-router'
import { Button } from '@/components/actions/Button/Button.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { actionLabels, explain } from '@/lib/errors.ts'

export function RouteError() {
  const { title, message, reference } = explain(useRouteError())
  return (
    <ErrorState variant="page" icon="error" title={title} message={message} reference={reference}>
      <Button onPress={() => window.location.reload()}>{actionLabels.retry}</Button>
    </ErrorState>
  )
}
