import { createFileRoute } from '@tanstack/react-router'
import DeploymentPage from './-deploymentPage'

export const Route = createFileRoute('/deployments/$siteName/')({
  component: DeploymentPage,
})
