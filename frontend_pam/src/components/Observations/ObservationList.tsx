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
import { getData } from "@/utils/FetchFunctions";
import { useQuery } from "@tanstack/react-query";
import { FaPlay } from "react-icons/fa";
import ObservationEditModal from './ObservationEditModal';

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
}

interface DataFile {
  id: string | number;
  file_name: string;
  file_format: string;
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
        // Process the observations to ensure taxon data is properly structured
        return observations.map(obs => {
          // If taxon is a number (ID), fetch the full taxon data
          if (typeof obs.taxon === 'number') {
            return {
              ...obs,
              id: Number(obs.id),
              obs_dt: obs.obs_dt || new Date().toISOString(),
              needs_review: obs.source === 'auto_detect' || obs.extra_data?.auto_detected || obs.needs_review,
              taxon: { id: obs.taxon, species_name: '', species_common_name: '' }
            };
          }
          // If taxon is already an object, use it as is
          return {
            ...obs,
            id: Number(obs.id),
            obs_dt: obs.obs_dt || new Date().toISOString(),
            needs_review: obs.source === 'auto_detect' || obs.extra_data?.auto_detected || obs.needs_review,
            taxon: obs.taxon || { id: 0, species_name: '', species_common_name: '' }
          };
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
    if (obsData) {
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
    // Ensure taxon is an object with the full structure
    const processedObservation = {
      ...updatedObservation,
      taxon: typeof updatedObservation.taxon === 'number'
        ? { id: updatedObservation.taxon, species_name: '', species_common_name: '' }
        : updatedObservation.taxon || { id: 0, species_name: '', species_common_name: '' }
    };

    // Update the local state immediately
    setObservations(prevObservations => 
      prevObservations.map(obs => 
        obs.id === processedObservation.id ? processedObservation : obs
      )
    );
    
    // Close the modal first
    setIsEditModalOpen(false);
    
    // Then refetch after a short delay to ensure the UI updates
    setTimeout(async () => {
      try {
        const data = await getData(`observation/?data_files=${dataFileIdStr}`, authTokens.access);
        const observations = Array.isArray(data) ? data : data.results || [];
        // Process the observations to ensure taxon data is properly structured
        const processedData = observations.map(obs => {
          // If this is the observation we just updated, use the processed observation
          if (obs.id === processedObservation.id) {
            return processedObservation;
          }
          // Otherwise, process the taxon data as usual
          return {
            ...obs,
            id: Number(obs.id),
            obs_dt: obs.obs_dt || new Date().toISOString(),
            needs_review: obs.source === 'auto_detect' || obs.extra_data?.auto_detected || obs.needs_review,
            taxon: typeof obs.taxon === 'number' 
              ? { id: obs.taxon, species_name: '', species_common_name: '' }
              : obs.taxon || { id: 0, species_name: '', species_common_name: '' }
          };
        });
        setObservations(processedData);
      } catch (error) {
        console.error('Failed to refetch observations:', error);
      }
    }, 100);
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
        <>
          <div className="rounded-md border">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50 text-sm">
                  <th className="p-2 text-left">Time</th>
                  <th className="p-2 text-left">Species</th>
                  <th className="p-2 text-left">Source</th>
                  <th className="p-2 text-left">Review Status</th>
                  <th className="p-2 text-left">Duration</th>
                  <th className="p-2 text-left">Amplitude</th>
                  <th className="p-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {observations.map((observation) => (
                  <tr key={observation.id} className="border-b hover:bg-muted/50">
                    <td className="p-2">
                      <div>
                        <div className="font-medium">
                          {formatTime(observation.extra_data.start_time)}
                        </div>
                        <div className="text-sm text-gray-500">
                          Duration: {observation.extra_data.duration.toFixed(2)}s
                        </div>
                      </div>
                    </td>
                    <td className="p-2">
                      <div>
                        <div className="font-medium">{observation.taxon.species_name}</div>
                        <div className="text-sm text-gray-500">{observation.taxon.species_common_name}</div>
                      </div>
                    </td>
                    <td className="p-2">{observation.source}</td>
                    <td className="p-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        observation.needs_review
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {observation.needs_review ? 'Not Reviewed' : 'Reviewed'}
                      </span>
                    </td>
                    <td className="p-2">{observation.extra_data.duration.toFixed(2)}s</td>
                    <td className="p-2">{observation.extra_data.avg_amplitude.toFixed(4)}</td>
                    <td className="p-2">
                      <div className="flex items-center gap-2">
                        <AudioPlayer
                          deviceId={deviceId}
                          fileId={dataFileId}
                          className="ml-2"
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditClick(observation)}
                          className="flex items-center gap-1"
                        >
                          <span>Edit</span>
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ObservationEditModal
            observation={selectedObservation}
            isOpen={isEditModalOpen}
            onClose={() => setIsEditModalOpen(false)}
            onSave={handleSaveObservation}
          />
        </>
      )}
    </div>
  );
}