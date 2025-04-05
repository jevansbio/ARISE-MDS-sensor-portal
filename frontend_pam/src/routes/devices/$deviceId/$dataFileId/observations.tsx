import { createFileRoute } from '@tanstack/react-router'
import ObservationList from '../../../../components/Observations/ObservationList'

export const Route = createFileRoute('/devices/$deviceId/$dataFileId/observations')({
  component: ObservationList,
  loader: ({ params }) => {
    console.log('Loading observations data with params:', params);
    return { deviceId: params.deviceId, dataFileId: params.dataFileId };
  }
}) 