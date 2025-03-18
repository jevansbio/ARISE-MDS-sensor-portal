import { createFileRoute } from '@tanstack/react-router';
import DeviceDetailPage from './-devicePage';
import { audioFilesQueryOptions, deviceQueryOptions } from '@/api/query';

export const Route = createFileRoute('/devices/$deviceId/')({
  loader: async ({ params: { deviceId }, context: { queryClient } }) => {
    await queryClient.prefetchQuery(deviceQueryOptions(deviceId));
    await queryClient.prefetchQuery(audioFilesQueryOptions(deviceId));
    return { deviceId };
  },
  component: DeviceDetailPage,
});