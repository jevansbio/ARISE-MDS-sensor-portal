import { useState, useEffect } from "react";
import { Route as ObservationsRoute } from "@/routes/devices/$deviceId/$dataFileId/observations";
import { useNavigate, useParams } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import AudioPlayer from "@/components/AudioPlayer/AudioPlayer";
import AudioWaveformPlayer from "@/components/AudioWaveformPlayer/AudioWaveformPlayer";
import { formatTime } from "@/utils/timeFormat";
import { useContext } from 'react';
import AuthContext from "@/auth/AuthContext";
import { getData, postData, patchData } from "@/utils/FetchFunctions";
import { useQuery } from "@tanstack/react-query";
import { FaPlay } from "react-icons/fa";
import ObservationEditModal from './ObservationEditModal';
import { useQueryClient } from "@tanstack/react-query";
import { ObservationTable } from './ObservationTable';
import { type Observation } from './types';

interface DataFile {
  id: string | number;
  file_name: string;
  file_format: string;
  file_length: number;
}

interface Device {
  id: string | number;
  name: string;
}

export default function ObservationList() {
  const { deviceId: deviceIdStr, dataFileId: dataFileIdStr } = useParams({ from: '/devices/$deviceId/$dataFileId' });
  const deviceId = deviceIdStr;  // Keep as string for API calls
  const dataFileId = dataFileIdStr;  // Keep as string for API calls
  const navigate = useNavigate();
  const { authTokens } = useContext(AuthContext) as any;
  const [selectedObservation, setSelectedObservation] = useState<Observation | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [taxonCache, setTaxonCache] = useState<Record<number, { id: number; species_name: string; species_common_name: string }>>({});
  const queryClient = useQueryClient();

  console.log('ObservationList mounted with params:', { deviceId, dataFileId });

  // Query for device details
  const { data: device, isLoading: isLoadingDevice } = useQuery({
    queryKey: ['device', deviceIdStr],
    queryFn: async () => {
      if (!deviceIdStr || !authTokens?.access) return null;
      const data = await getData(`devices/${deviceIdStr}`, authTokens.access);
      return data as Device;
    },
    enabled: !!deviceIdStr && !!authTokens?.access,
    retry: 1
  });

  // Query for data file details
  const { data: dataFile, isLoading: isLoadingFile, error: fileError } = useQuery({
    queryKey: ['dataFile', deviceIdStr, dataFileIdStr],
    queryFn: async () => {
      if (!deviceIdStr || !dataFileIdStr || !authTokens?.access) return null;
      const data = await getData(`devices/${deviceIdStr}/datafiles/${dataFileIdStr}`, authTokens.access);
      return data as DataFile;
    },
    enabled: !!deviceIdStr && !!dataFileIdStr && !!authTokens?.access,
    retry: 1
  });

  // Query for observations
  const { data: observations = [], isLoading: isLoadingObs, error: obsError } = useQuery({
    queryKey: ['observations', dataFileIdStr],
    queryFn: async () => {
      if (!deviceIdStr || !dataFileIdStr || !authTokens?.access) return [];
      try {
        // Fetch all pages of observations
        let allObservations: any[] = [];
        let page = 1;
        let hasMore = true;
        
        while (hasMore) {
          const data = await getData(`observation/?data_files=${dataFileIdStr}&page=${page}&page_size=50`, authTokens.access);
          const pageObservations = Array.isArray(data) ? data : data.results || [];
          allObservations = [...allObservations, ...pageObservations];
          
          // Check if there are more pages
          hasMore = data.next !== null;
          page++;
        }
        
        // Process observations first to extract taxon data
        const processedObservations: Observation[] = allObservations.map((obs: any) => {
          // If taxon is already an object with complete data, use it directly
          if (obs.taxon && typeof obs.taxon === 'object' && obs.taxon.species_name) {
            // Update taxon cache with this data
            setTaxonCache(prev => ({
              ...prev,
              [obs.taxon.id]: {
                id: obs.taxon.id,
                species_name: obs.taxon.species_name,
                species_common_name: obs.taxon.species_common_name
              }
            }));
            return {
              ...obs,
              id: Number(obs.id),
              obs_dt: obs.obs_dt || new Date().toISOString(),
              needs_review: obs.needs_review,
              taxon: {
                id: obs.taxon.id,
                species_name: obs.taxon.species_name,
                species_common_name: obs.taxon.species_common_name
              }
            };
          }
          
          // If taxon is a number (ID), try to use cached data first
          const taxonId = typeof obs.taxon === 'number' ? obs.taxon : obs.taxon?.id;
          if (taxonId && taxonCache[taxonId]) {
            return {
              ...obs,
              id: Number(obs.id),
              obs_dt: obs.obs_dt || new Date().toISOString(),
              needs_review: obs.needs_review,
              taxon: {
                id: taxonId,
                species_name: taxonCache[taxonId].species_name,
                species_common_name: taxonCache[taxonId].species_common_name
              }
            };
          }
          
          // Default case for missing taxon data
          return {
            ...obs,
            id: Number(obs.id),
            obs_dt: obs.obs_dt || new Date().toISOString(),
            needs_review: obs.needs_review,
            taxon: { 
              id: taxonId || 0, 
              species_name: obs.taxon?.species_name || 'Unknown', 
              species_common_name: obs.taxon?.species_common_name || 'Unknown' 
            }
          };
        });
        
        return processedObservations;
      } catch (error) {
        console.error('Failed to fetch observations:', error);
        throw error;
      }
    },
    enabled: !!deviceIdStr && !!dataFileIdStr && !!authTokens?.access,
    gcTime: 5 * 60 * 1000, // Keep cache for 5 minutes
    staleTime: 1 * 60 * 1000, // Consider data fresh for 1 minute
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true
  });

  const isLoading = isLoadingDevice || isLoadingFile || isLoadingObs;
  const error = fileError || obsError;

  if (!deviceId || !dataFileId) {
    console.error('Missing route parameters:', { deviceId, dataFileId });
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
        Missing required parameters: deviceId and dataFileId must be provided
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
    if (!deviceIdStr || !dataFileIdStr) return;
    navigate({ to: "/devices/$deviceId/$dataFileId", params: { deviceId: deviceIdStr, dataFileId: dataFileIdStr } });
  };

  const handleEditClick = (observation: Observation) => {
    setSelectedObservation(observation);
    setIsEditModalOpen(true);
  };

  const handleSaveObservation = async (updatedObservation: Observation) => {
    console.log('handleSaveObservation called with:', updatedObservation);
    
    // Store current data for potential rollback
    const currentData = queryClient.getQueryData(['observations', dataFileIdStr]) as Observation[];
    
    // Update taxon cache with the new taxon data
    if (updatedObservation.taxon) {
      setTaxonCache(prev => ({
        ...prev,
        [updatedObservation.taxon.id]: {
          id: updatedObservation.taxon.id,
          species_name: updatedObservation.taxon.species_name,
          species_common_name: updatedObservation.taxon.species_common_name
        }
      }));
    }
    
    // Close edit modal
    setIsEditModalOpen(false);
    console.log('Edit modal closed');
    
    // Optimistically update the query cache
    queryClient.setQueryData(['observations', dataFileIdStr], (old: any) => {
      if (!old) return [updatedObservation];
      return old.map((obs: Observation) => 
        obs.id === updatedObservation.id ? updatedObservation : obs
      );
    });
    
    // Invalidate and refetch observations query
    console.log('Invalidating queries...');
    await queryClient.invalidateQueries({ 
      queryKey: ['observations', dataFileIdStr],
      refetchType: 'active'
    });
    
    // Wait for the refetch to complete
    console.log('Waiting for refetch to complete...');
    await queryClient.refetchQueries({ 
      queryKey: ['observations', dataFileIdStr],
      type: 'active'
    });
    
    // Get the current data after refetch
    const newData = queryClient.getQueryData(['observations', dataFileIdStr]) as Observation[];
    console.log('Current data after refetch:', newData);
    
    if (!newData) {
      console.error('No data available after refetch');
      return;
    }
    
    // Log all observation IDs for debugging
    console.log('All observation IDs:', newData.map(obs => obs.id));
    
    // Find the updated observation
    const updatedObs = newData.find((obs) => obs.id === updatedObservation.id);
    console.log('Updated observation found:', updatedObs);
    
    if (!updatedObs) {
      console.error('Updated observation not found in current data');
      // Try to find the observation in the original data
      const originalObs = currentData?.find(obs => obs.id === updatedObservation.id);
      console.log('Original observation:', originalObs);
      return;
    }
    
    // Verify the species name matches
    if (updatedObs.taxon?.species_name !== updatedObservation.taxon?.species_name) {
      console.error('Species name mismatch:', {
        expected: updatedObservation.taxon?.species_name,
        actual: updatedObs.taxon?.species_name
      });
      return;
    }
    
    console.log('Observation update verified successfully');
  };

  const handleDeleteObservation = async (id: number) => {
    if (!authTokens?.access) return;
    
    if (!window.confirm('Are you sure you want to delete this observation?')) {
      return;
    }

    try {
      // First, get the observation details to get the taxon information
      const observationResponse = await fetch(`/api/observation/${id}/`, {
        headers: {
          'Authorization': `Bearer ${authTokens.access}`
        }
      });

      if (!observationResponse.ok) {
        throw new Error('Failed to fetch observation details');
      }

      const observation = await observationResponse.json();
      const speciesName = observation.taxon.species_name;

      // Create a temporary observation with the same taxon
      const tempObservationResponse = await fetch('/api/observation/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authTokens.access}`
        },
        body: JSON.stringify({
          taxon: {
            id: observation.taxon.id,
            species_name: observation.taxon.species_name,
            species_common_name: observation.taxon.species_common_name
          }
        })
      });

      if (!tempObservationResponse.ok) {
        throw new Error('Failed to create temporary observation');
      }

      const tempObservation = await tempObservationResponse.json();

      // Replace the original observation with the temporary one
      const replaceResponse = await fetch(`/api/observation/${id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authTokens.access}`
        },
        body: JSON.stringify({
          taxon: {
            id: tempObservation.taxon.id,
            species_name: tempObservation.taxon.species_name,
            species_common_name: tempObservation.taxon.species_common_name
          }
        })
      });

      if (!replaceResponse.ok) {
        throw new Error('Failed to replace observation');
      }

      // Invalidate and refetch the observations query immediately
      await queryClient.invalidateQueries({ queryKey: ['observations', dataFileIdStr] });
      await queryClient.refetchQueries({ queryKey: ['observations', dataFileIdStr] });

      console.log('=== handleDeleteObservation completed successfully ===');
    } catch (error) {
      console.error('Error in handleDeleteObservation:', error);
      throw error;
    }
  };

  return (
    <div className="container mx-auto py-10 space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Observations</h2>
          {device && dataFile && (
            <p className="text-gray-600">
              for {dataFile.file_name} on {device.name}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button onClick={handleBack}>Back to File</Button>
        </div>
      </div>

      {observations.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <p className="text-gray-500 text-lg">No observations found</p>
        </div>
      ) : (
        <ObservationTable
          deviceId={deviceId}
          fileId={dataFileId}
          fileFormat={dataFile?.file_format || 'wav'}
          fileDuration={dataFile?.file_length || 0}
          observations={observations}
          onDelete={handleDeleteObservation}
          onEdit={handleEditClick}
        />
      )}

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