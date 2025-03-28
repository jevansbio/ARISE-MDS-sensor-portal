import { createFileRoute } from '@tanstack/react-router'
import DevicePage from './-devicePage'

export const Route = createFileRoute('/devices/$deviceId/')({
  component: DevicePage,
})
