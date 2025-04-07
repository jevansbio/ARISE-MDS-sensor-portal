import { createFileRoute } from '@tanstack/react-router';
import DeploymentsPage from './-deploymentsPage';

export const Route = createFileRoute('/deployments/')({
  component: DeploymentsPage,
});
