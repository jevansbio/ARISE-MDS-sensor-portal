import { createFileRoute } from '@tanstack/react-router';
import DevicesPage from './-devicesPage';
import { devicesQueryOptions } from '@/api/query';

export const Route = createFileRoute('/devices/')({
  loader: async ({ context: { queryClient } }) =>
    await queryClient.prefetchQuery(devicesQueryOptions),
  component: DevicesPage,
});
