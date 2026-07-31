/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from '@tanstack/react-router'

function Support() {
  return <div>Hello "/support"!</div>
}

export const Route = createFileRoute('/support')({
  component: Support,
})
