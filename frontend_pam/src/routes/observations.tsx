import { createFileRoute } from '@tanstack/react-router';
import AllObservationsList from '@/components/Observations/AllObservationsList';

export const Route = createFileRoute('/observations')({
  component: ObservationsPage,
});

function ObservationsPage() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">All Observations</h1>
      <AllObservationsList />
    </div>
  );
} 