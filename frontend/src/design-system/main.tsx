// Entry point of the review page, design-system.html. It mounts on its own: no router, sign-in or
// backend. `vite build` leaves it out, so it never ships.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { DesignSystem } from '@/design-system/DesignSystem.tsx'
import '@/styles/base.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <DesignSystem />
  </StrictMode>,
)
