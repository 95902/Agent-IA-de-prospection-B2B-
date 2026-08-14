/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_app')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/_app"!</div>
}
