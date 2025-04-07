import { createFileRoute } from '@tanstack/react-router'
import DevicePage from './-devicePage'

export const Route = createFileRoute('/deployments/$site_name/')({
  component: DevicePage,
})
