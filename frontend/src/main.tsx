// Entry point: mounts the app into the #root element of index.html, inside the query cache, React
// Aria's link handling, the router and the toasts
import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { RouterProvider as AriaRouterProvider } from 'react-aria-components'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import '@/styles/base.css'
import { routes } from '@/app/routes.tsx'
import { ToastRegion } from '@/app/ToastRegion.tsx'
import { queryClient } from '@/lib/queryClient.ts'

const router = createBrowserRouter(routes)

// React Aria's links go through React Router, so following one loads no page. One function for the
// page's life, as React Aria's provider memoises on it.
function navigate(path: string) {
  void router.navigate(path)
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AriaRouterProvider navigate={navigate}>
        <RouterProvider router={router} />
        <ToastRegion />
      </AriaRouterProvider>
    </QueryClientProvider>
  </StrictMode>,
)
