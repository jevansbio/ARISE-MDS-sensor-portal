import { createFileRoute } from '@tanstack/react-router';
import DevicesPage from './-devicesPage';

export const Route = createFileRoute('/devices/')({
  component: DevicesPage,
});
