/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from '@tanstack/react-router'

function Parameters() {
  return <div>Hello "/parametres"!</div>
}

export const Route = createFileRoute('/parametre')({
  component: Parameters,
})
