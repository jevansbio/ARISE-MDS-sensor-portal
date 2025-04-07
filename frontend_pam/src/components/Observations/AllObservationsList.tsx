import { useState, useContext } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { getData } from "@/utils/FetchFunctions";
import AuthContext from "@/auth/AuthContext";
import ObservationEditModal from './ObservationEditModal';
import { formatTime } from "@/utils/timeFormat";

interface Observation {
  id: number;
  obs_dt: string;
  taxon: {
    species_name: string;
    species_common_name: string;
    id: number;
  };
  source: string;
  needs_review: boolean;
  extra_data: {
    start_time: number;
    end_time: number;
    duration: number;
    avg_amplitude: number;
    auto_detected: boolean;
  };
  data_file?: {
    id: number;
    file_name: string;
  };
}

export default function AllObservationsList() {
  const { authTokens } = useContext(AuthContext) as any;
  const [selectedObservation, setSelectedObservation] = useState<Observation | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [taxonCache, setTaxonCache] = useState<Record<number, { id: number; species_name: string; species_common_name: string }>>({});
  const queryClient = useQueryClient();

  // Query for all observations
  const { data: observations, isLoading } = useQuery({
    queryKey: ['all-observations'],
    queryFn: async () => {
      if (!authTokens?.access) return [];
      try {
        const data = await getData('observation/', authTokens.access);
        const observations = Array.isArray(data) ? data : data.results || [];
        
        // Process observations to extract taxon data
        const processedObservations = observations.map((obs: any) => {
          if (obs.taxon && typeof obs.taxon === 'object') {
            const taxonId = obs.taxon.id;
            if (taxonId) {
              setTaxonCache(prev => ({ ...prev, [taxonId]: obs.taxon }));
            }
            return {
              ...obs,
              id: Number(obs.id),
              obs_dt: obs.obs_dt || new Date().toISOString(),
              needs_review: obs.needs_review,
              taxon: obs.taxon
            };
          }
          
          const taxonId = typeof obs.taxon === 'number' ? obs.taxon : obs.taxon?.id;
          if (taxonId && taxonCache[taxonId]) {
            return {
              ...obs,
              id: Number(obs.id),
              obs_dt: obs.obs_dt || new Date().toISOString(),
              needs_review: obs.needs_review,
              taxon: taxonCache[taxonId]
            };
          }
          
          return {
            ...obs,
            id: Number(obs.id),
            obs_dt: obs.obs_dt || new Date().toISOString(),
            needs_review: obs.needs_review,
            taxon: { id: taxonId || 0, species_name: 'Unknown', species_common_name: 'Unknown' }
          };
        });
        
        // Fetch missing taxon data
        const taxonFetchPromises = processedObservations
          .filter((obs: any) => typeof obs.taxon === 'number' && !taxonCache[obs.taxon])
          .map(async (obs: any) => {
            const taxonId = obs.taxon as number;
            try {
              const taxonData = await getData(`taxon/${taxonId}/`, authTokens.access);
              setTaxonCache(prev => ({ ...prev, [taxonId]: taxonData }));
              return { taxonId, taxonData };
            } catch (error) {
              console.error(`Failed to fetch taxon data for ID ${taxonId}:`, error);
              return { taxonId, taxonData: null };
            }
          });
        
        await Promise.all(taxonFetchPromises);
        
        return processedObservations.map((obs: any) => {
          const taxonId = typeof obs.taxon === 'number' ? obs.taxon : obs.taxon?.id;
          if (taxonId && taxonCache[taxonId]) {
            return {
              ...obs,
              taxon: taxonCache[taxonId]
            };
          }
          return obs;
        });
      } catch (error) {
        console.error('Failed to fetch observations:', error);
        throw error;
      }
    },
    enabled: !!authTokens?.access,
    refetchOnMount: true,
    refetchOnWindowFocus: true
  });

  const handleEditClick = (observation: Observation) => {
    setSelectedObservation(observation);
    setIsEditModalOpen(true);
  };

  const handleSaveObservation = async (updatedObservation: Observation) => {
    try {
      setTaxonCache(prev => ({
        ...prev,
        [updatedObservation.taxon.id]: {
          id: updatedObservation.taxon.id,
          species_name: updatedObservation.taxon.species_name,
          species_common_name: updatedObservation.taxon.species_common_name
        }
      }));

      setIsEditModalOpen(false);

      // Update the query cache
      queryClient.setQueryData(['all-observations'], (oldData: any) => {
        if (!oldData) return oldData;
        return oldData.map((obs: any) => 
          obs.id === updatedObservation.id ? {
            ...updatedObservation,
            taxon: {
              id: updatedObservation.taxon.id,
              species_name: updatedObservation.taxon.species_name,
              species_common_name: updatedObservation.taxon.species_common_name
            }
          } : obs
        );
      });
    } catch (error) {
      console.error('Error saving observation:', error);
    }
  };

  if (isLoading) {
    return <div>Loading observations...</div>;
  }

  return (
    <div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date/Time</TableHead>
            <TableHead>Species</TableHead>
            <TableHead>Common Name</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Review Status</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>File</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {observations?.map((observation: Observation) => (
            <TableRow key={observation.id}>
              <TableCell>{new Date(observation.obs_dt).toLocaleString()}</TableCell>
              <TableCell>{observation.taxon.species_name}</TableCell>
              <TableCell>{observation.taxon.species_common_name}</TableCell>
              <TableCell>{observation.source}</TableCell>
              <TableCell>{observation.needs_review ? "Needs Review" : "Reviewed"}</TableCell>
              <TableCell>
                {observation.extra_data?.duration ? 
                  formatTime(observation.extra_data.duration) : 
                  "N/A"}
              </TableCell>
              <TableCell>
                {observation.data_file?.file_name || "N/A"}
              </TableCell>
              <TableCell>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEditClick(observation)}
                >
                  Edit
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selectedObservation && (
        <ObservationEditModal
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          observation={selectedObservation}
          onSave={handleSaveObservation}
        />
      )}
    </div>
  );
} 