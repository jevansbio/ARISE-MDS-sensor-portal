import { useSuspenseQuery } from '@tanstack/react-query';
import { deviceQueryOptions } from '@/api/query';
import { Route } from '.';

export default function DeviceDetailPage() {

  const { deviceId } = Route.useParams();

  const { data: device } = useSuspenseQuery(deviceQueryOptions(deviceId));

  return (
      <div>
        <h2>Device Details</h2>
        <p>ID: {device.id}</p>
        <p>TEST 123</p>
        {/* Render additional device details as needed */}
      </div>
  )
}