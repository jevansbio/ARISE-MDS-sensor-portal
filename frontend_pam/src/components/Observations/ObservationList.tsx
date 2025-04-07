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
  const [observations, setObservations] = useState<Observation[]>([]);
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
  const { data: obsData, isLoading: isLoadingObs, error: obsError, refetch: refetchObs } = useQuery({
    queryKey: ['observations', dataFileIdStr],
    queryFn: async () => {
      if (!deviceIdStr || !dataFileIdStr || !authTokens?.access) return null;
      try {
        const data = await getData(`observation/?data_files=${dataFileIdStr}`, authTokens.access);
        const observations = Array.isArray(data) ? data : data.results || [];
        
        // Process observations first to extract taxon data
        const processedObservations = observations.map((obs: any) => {
          // If taxon is already an object, use it directly and cache it
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
          
          // If taxon is a number (ID), try to use cached data first
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
          
          // Default case for missing taxon data
          return {
            ...obs,
            id: Number(obs.id),
            obs_dt: obs.obs_dt || new Date().toISOString(),
            needs_review: obs.needs_review,
            taxon: { id: taxonId || 0, species_name: 'Unknown', species_common_name: 'Unknown' }
          };
        });
        
        // Only fetch taxon data for observations that need it
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
        
        // Wait for taxon fetches to complete
        await Promise.all(taxonFetchPromises);
        
        // Update observations with fetched taxon data
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
    enabled: !!deviceIdStr && !!dataFileIdStr && !!authTokens?.access,
    gcTime: 5 * 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: true
  });

  // Update observations state when data changes
  useEffect(() => {
    console.log('=== Observations useEffect triggered ===');
    console.log('Current obsData:', obsData);
    if (obsData) {
      console.log('Setting observations state with:', obsData);
      setObservations(obsData);
    }
  }, [obsData]);

  const handleBack = () => {
    if (!deviceIdStr || !dataFileIdStr) return;
    navigate({ to: "/devices/$deviceId/$dataFileId", params: { deviceId: deviceIdStr, dataFileId: dataFileIdStr } });
  };

  const handleEditClick = (observation: Observation) => {
    setSelectedObservation(observation);
    setIsEditModalOpen(true);
  };

  const handleSaveObservation = async (updatedObservation: Observation) => {
    console.log('=== Starting handleSaveObservation ===');
    console.log('Updated observation received:', updatedObservation);
    
    try {
      // Update the taxon cache first
      console.log('Updating taxon cache with:', updatedObservation.taxon);
      setTaxonCache(prev => {
        const newCache = {
          ...prev,
          [updatedObservation.taxon.id]: {
            id: updatedObservation.taxon.id,
            species_name: updatedObservation.taxon.species_name,
            species_common_name: updatedObservation.taxon.species_common_name
          }
        };
        console.log('New taxon cache:', newCache);
        return newCache;
      });

      // Update the local state immediately
      console.log('Updating local state with:', updatedObservation);
      setObservations(prev => {
        const newObservations = prev.map(obs => 
          obs.id === updatedObservation.id ? {
            ...updatedObservation,
            taxon: {
              id: updatedObservation.taxon.id,
              species_name: updatedObservation.taxon.species_name,
              species_common_name: updatedObservation.taxon.species_common_name
            }
          } : obs
        );
        console.log('New observations state:', newObservations);
        return newObservations;
      });

      // Close the modal
      setIsEditModalOpen(false);
      console.log('Modal closed');

      // Update the query cache instead of refetching
      queryClient.setQueryData(['observations', dataFileIdStr], (oldData: any) => {
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

      console.log('=== handleSaveObservation completed successfully ===');
    } catch (error) {
      console.error('=== Error in handleSaveObservation ===');
      console.error('Error details:', error);
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        // Show error message to user
        alert('Failed to update observation. Please try again.');
      }
    }
  };

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
        <Button onClick={handleBack}>Back to File</Button>
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
          onDelete={(id: number) => console.log('Delete observation:', id)}
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