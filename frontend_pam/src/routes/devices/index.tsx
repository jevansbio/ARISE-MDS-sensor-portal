import { createFileRoute } from '@tanstack/react-router';
import DevicesPage from './-deploymentsPage';

export const Route = createFileRoute('/devices/')({
  component: DevicesPage,
});
