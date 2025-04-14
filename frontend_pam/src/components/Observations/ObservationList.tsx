import { useState, useEffect, useContext } from "react";
import { useNavigate, useParams } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import AudioPlayer from "@/components/AudioPlayer/AudioPlayer";
import AudioWaveformPlayer from "@/components/AudioWaveformPlayer/AudioWaveformPlayer";
import { formatTime } from "@/utils/timeFormat";
import AuthContext from "@/auth/AuthContext";
import { getData, postData, patchData } from "@/utils/FetchFunctions";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FaPlay } from "react-icons/fa";
import ObservationEditModal from './ObservationEditModal';
import { ObservationTable } from './ObservationTable';
import { type Observation } from '@/types';

export default function ObservationList() {
  const { siteName, dataFileId } = useParams({ from: '/deployments/$siteName/$dataFileId/observations' });
  const navigate = useNavigate();
  const { authTokens } = useContext(AuthContext) as any;
  const [selectedObservation, setSelectedObservation] = useState<Observation | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const queryClient = useQueryClient();

  console.log('ObservationList mounted with params:', { siteName, dataFileId });

  // Query for data file details
  const { data: dataFile, isLoading: isLoadingFile, error: fileError } = useQuery({
    queryKey: ['dataFile', siteName, dataFileId],
    queryFn: async () => {
      if (!siteName || !dataFileId || !authTokens?.access) return null;
      const data = await getData(`deployments/${siteName}/datafiles/${dataFileId}`, authTokens.access);
      return data;
    },
    enabled: !!siteName && !!dataFileId && !!authTokens?.access,
    retry: 1
  });

  // Custom hook for fetching taxon data
  const useTaxon = (taxonId: number | undefined) => {
    return useQuery({
      queryKey: ['taxon', taxonId],
      queryFn: async () => {
        if (!taxonId || !authTokens?.access) return null;
        try {
          const data = await getData(`taxon/${taxonId}/`, authTokens.access);
          if (!data || !data.species_name) {
            console.warn(`Invalid taxon data received for ID ${taxonId}`);
            return null;
          }
          return {
            id: taxonId,
            species_name: data.species_name,
            species_common_name: data.species_common_name || 'Unknown'
          };
        } catch (error) {
          console.error(`Failed to fetch taxon data for ID ${taxonId}:`, error);
          return null;
        }
      },
      enabled: !!taxonId && !!authTokens?.access,
      staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
      gcTime: 10 * 60 * 1000, // Keep unused data in cache for 10 minutes
    });
  };

  // Query for observations
  const { data: observations = [], isLoading: isLoadingObs, error: obsError } = useQuery<Observation[]>({
    queryKey: ['observations', dataFileId],
    queryFn: async () => {
      if (!siteName || !dataFileId || !authTokens?.access) return [];
      try {
        console.log('Fetching observations for data file:', dataFileId);
        // Fetch all pages of observations
        let allObservations: any[] = [];
        let page = 1;
        let hasMore = true;
        
        while (hasMore) {
          console.log(`Fetching page ${page} of observations...`);
          const data = await getData(`observation/?data_files=${dataFileId}&page=${page}&page_size=50`, authTokens.access);
          const pageObservations = Array.isArray(data) ? data : data.results || [];
          console.log(`Retrieved ${pageObservations.length} observations from page ${page}`);
          allObservations = [...allObservations, ...pageObservations];
          
          // Check if there are more pages
          hasMore = data.next !== null;
          page++;
        }
        
        console.log(`Total observations fetched: ${allObservations.length}`);
        
        // Process observations with taxon data
        const processedObservations: Observation[] = allObservations.map((obs: any) => {
          // Ensure taxon data is properly structured
          let taxonData = {
            id: 0,
            species_name: 'Unknown',
            species_common_name: 'Unknown'
          };

          if (obs.taxon) {
            if (typeof obs.taxon === 'number') {
              taxonData.id = obs.taxon;
            } else if (typeof obs.taxon === 'object') {
              taxonData = {
                id: obs.taxon.id || 0,
                species_name: obs.taxon.species_name || 'Unknown',
                species_common_name: obs.taxon.species_common_name || 'Unknown'
              };
            }
          }

          return {
            ...obs,
            id: Number(obs.id),
            obs_dt: obs.obs_dt || new Date().toISOString(),
            needs_review: obs.needs_review || false,
            taxon: taxonData
          };
        });
        
        console.log('Processed observations:', processedObservations.length);
        return processedObservations;
      } catch (error) {
        console.error('Failed to fetch observations:', error);
        throw error;
      }
    },
    enabled: !!siteName && !!dataFileId && !!authTokens?.access,
    gcTime: 5 * 60 * 1000, // Keep cache for 5 minutes
    staleTime: 0, // Always consider data stale to force refetch
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: 3, // Retry failed requests up to 3 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000) // Exponential backoff
  });

  // Effect to handle component mount and data file changes
  useEffect(() => {
    if (!siteName || !dataFileId || !authTokens?.access) return;
    
    console.log('Component mounted or data file changed:', { siteName, dataFileId });
    
    // Force a refetch of observations when the component mounts or data file changes
    queryClient.invalidateQueries({ 
      queryKey: ['observations', dataFileId],
      refetchType: 'active'
    });
  }, [siteName, dataFileId, authTokens?.access, queryClient]);

  const isLoading = isLoadingFile || isLoadingObs;
  const error = fileError || obsError;

  if (!siteName || !dataFileId) {
    console.error('Missing route parameters:', { siteName, dataFileId });
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
        Missing required parameters: siteName and dataFileId must be provided
      </div>
    );
  }

  if (!authTokens?.access) {
    return (
      <div className="p-4 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded">
        Please log in to view observations
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-4 text-blue-700">
        Loading observations...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
        {error instanceof Error ? error.message : 'Failed to load observations'}
      </div>
    );
  }

  const handleBack = () => {
    if (!siteName || !dataFileId) return;
    navigate({ 
      to: "/deployments/$siteName/$dataFileId", 
      params: { siteName, dataFileId },
      search: { observationId: undefined }
    });
  };

  const handleEditClick = (observation: Observation) => {
    setSelectedObservation(observation);
    setIsEditModalOpen(true);
  };

  const handleSaveObservation = async (updatedObservation: Observation) => {
    console.log('handleSaveObservation called with:', updatedObservation);
    
    try {
      // Close edit modal
      setIsEditModalOpen(false);
      console.log('Edit modal closed');
      
      // Update the observation in the backend
      if (!authTokens?.access) {
        throw new Error('No authentication token available');
      }
      
      // Format the taxon data correctly
      const formattedObservation = {
        ...updatedObservation,
        taxon: {
          id: updatedObservation.taxon.id,
          species_name: updatedObservation.taxon.species_name,
          species_common_name: updatedObservation.taxon.species_common_name
        }
      };
      
      const response = await patchData(
        `observation/${updatedObservation.id}/`,
        authTokens.access,
        formattedObservation
      );
      
      if (!response.ok) {
        throw new Error('Failed to update observation');
      }
      
      // Invalidate and refetch observations
      await queryClient.invalidateQueries({ queryKey: ['observations', dataFileId] });
      console.log('Observations cache invalidated');
      
    } catch (error) {
      console.error('Error saving observation:', error);
      // Reopen the modal if there was an error
      setIsEditModalOpen(true);
      throw error;
    }
  };

  const handleDeleteObservation = async (id: number) => {
    try {
      if (!authTokens?.access) {
        throw new Error('No authentication token available');
      }
      
      const response = await postData(
        `observation/${id}/delete/`,
        authTokens.access,
        {}
      );
      
      if (!response.ok) {
        throw new Error('Failed to delete observation');
      }
      
      // Invalidate and refetch observations
      await queryClient.invalidateQueries({ queryKey: ['observations', dataFileId] });
      
    } catch (error) {
      console.error('Error deleting observation:', error);
      throw error;
    }
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Observations</h1>
        <Button onClick={handleBack} variant="outline">Back to Data File</Button>
      </div>

      <ObservationTable
        deviceId={siteName}
        fileId={dataFileId}
        fileFormat={dataFile?.file_format || 'wav'}
        fileDuration={dataFile?.file_length || 0}
        observations={observations}
        onEdit={handleEditClick}
        onDelete={handleDeleteObservation}
      />

      {isEditModalOpen && selectedObservation && (
        <ObservationEditModal
          isOpen={isEditModalOpen}
          observation={selectedObservation}
          onSave={handleSaveObservation}
          onClose={() => setIsEditModalOpen(false)}
        />
      )}
    </div>
  );
}