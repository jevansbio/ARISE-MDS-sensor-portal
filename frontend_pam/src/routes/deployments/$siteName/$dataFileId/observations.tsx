import { createFileRoute } from '@tanstack/react-router'
import ObservationList from '@/components/Observations/ObservationList'

export const Route = createFileRoute('/deployments/$siteName/$dataFileId/observations')({
  component: () => <ObservationList />,
  loader: ({ params }) => {
    console.log('Loading observations data with params:', params);
    return { siteName: params.siteName, dataFileId: params.dataFileId };
  }
}) 