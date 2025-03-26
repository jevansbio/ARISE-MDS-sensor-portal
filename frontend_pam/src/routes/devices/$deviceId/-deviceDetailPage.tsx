import { useSuspenseQuery } from '@tanstack/react-query';
import { deviceQueryOptions } from '@/api/query';
import { Route } from '.';

export default function DeviceDetailPage() {

  const { deviceId } = Route.useParams();

  const { data: device } = useSuspenseQuery(deviceQueryOptions(deviceId));

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Device Details</h2>
      <div className="grid grid-cols-2 gap-x-8 gap-y-4">
        <p>
          <strong>Device ID:</strong> {device.id}
        </p>
        <p>
          <strong>Deployment ID:</strong> 
        </p>
        <p>
          <strong>Start date:</strong> {device.startDate}
        </p>
        <p>
          <strong>End date:</strong> {device.endDate}
        </p>
        <p>
          <strong>Last upload:</strong> {device.lastUpload}
        </p>
        <p>
          <strong>Folder size:</strong> {device.folderSize}
        </p>
        <p>
          <strong>Country:</strong> 
        </p>
        <p>
          <strong>Site:</strong> 
        </p>
        <p>
          <strong>Date:</strong> 
        </p>
        <p>
          <strong>Time:</strong> 
        </p>
        <p>
          <strong>Latitude:</strong> 
        </p>
        <p>
          <strong>Longitude:</strong> 
        </p>
        <p>
          <strong>Coordinate Uncertainty:</strong> 
        </p>
        <p>
          <strong>GPS device:</strong> 
        </p>
        <p>
          <strong>Microphone Height:</strong> 
        </p>
        <p>
          <strong>Microphone Direction:</strong> 
        </p>
        <p>
          <strong>Habitat:</strong> 
        </p>
        <p>
          <strong>Score:</strong> 
        </p>
        <p>
          <strong>Protocol Checklist:</strong> 
        </p>
        <p>
          <strong>Adresse e-mail:</strong> 
        </p>
        <p>
          <strong>Comment:</strong> 
        </p>
      </div>
    </div>
  );
}