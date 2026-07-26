/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from '@tanstack/react-router'

function Calls() {
  return <div>Hello "/appels"!</div>
}

export const Route = createFileRoute('/appels')({
  component: Calls,
})
