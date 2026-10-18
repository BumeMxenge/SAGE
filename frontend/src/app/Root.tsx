// The root of every page: it gives the browser tab the page's title from the route table, then shows
// the page
import { useEffect } from 'react'
import { Outlet, useMatches } from 'react-router'

export function Root() {
  // React Router types a route's handle as unknown, so it is read as the table writes it
  const handle = useMatches().at(-1)?.handle as { title: string } | undefined
  const title = handle?.title

  useEffect(() => {
    if (title) document.title = title
  }, [title])

  return <Outlet />
}
