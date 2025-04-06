import { useState, useEffect } from "react";
import { Route as ObservationsRoute } from "@/routes/devices/$deviceId/$dataFileId/observations";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import AudioPlayer from "@/components/AudioPlayer/AudioPlayer";
import AudioWaveformPlayer from "@/components/AudioWaveformPlayer/AudioWaveformPlayer";
import { formatTime } from "@/utils/timeFormat";
import { useContext } from 'react';
import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { useQuery } from "@tanstack/react-query";

interface Observation {
  id: number;
  obs_dt: string;
  taxon: {
    species_name: string;
    species_common_name: string;
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
  id: string;
  file_name: string;
  file_format: string;
}

interface Device {
  id: string;
  name: string;
}

export default function ObservationList() {
  const { deviceId, dataFileId } = ObservationsRoute.useParams();
  const navigate = useNavigate();
  const { authTokens } = useContext(AuthContext) as any;
  const [observations, setObservations] = useState<Observation[]>([]);

  console.log('ObservationList mounted with params:', { deviceId, dataFileId });

  // Query for device details
  const { data: device, isLoading: isLoadingDevice } = useQuery({
    queryKey: ['device', deviceId],
    queryFn: async () => {
      if (!deviceId || !authTokens?.access) {
        console.error('Missing deviceId or auth token for device query');
        return null;
      }
      console.log('Fetching device:', deviceId);
      const data = await getData(`devices/${deviceId}`, authTokens.access);
      return data as Device;
    },
    enabled: !!deviceId && !!authTokens?.access,
    retry: 1
  });

  // Query for data file details
  const { data: dataFile, isLoading: isLoadingFile, error: fileError } = useQuery({
    queryKey: ['dataFile', deviceId, dataFileId],
    queryFn: async () => {
      if (!deviceId || !dataFileId || !authTokens?.access) {
        console.error('Missing deviceId, dataFileId, or auth token for file query');
        return null;
      }
      console.log('Fetching data file:', { deviceId, dataFileId });
      const data = await getData(`devices/${deviceId}/datafiles/${dataFileId}`, authTokens.access);
      return data as DataFile;
    },
    enabled: !!deviceId && !!dataFileId && !!authTokens?.access,
    retry: 1
  });

  // Query for observations
  const { data: obsData, isLoading: isLoadingObs, error: obsError } = useQuery({
    queryKey: ['observations', dataFileId],
    queryFn: async () => {
      if (!deviceId || !dataFileId || !authTokens?.access) {
        console.error('Missing parameters for observations query');
        return null;
      }
      console.log('Fetching observations:', { deviceId, dataFileId });
      try {
        const data = await getData(`observation/?data_files=${dataFileId}`, authTokens.access);
        console.log('Observations data:', data);
        return Array.isArray(data) ? data : data.results || [];
      } catch (error) {
        console.error('Failed to fetch observations:', error);
        throw error;
      }
    },
    enabled: !!deviceId && !!dataFileId && !!authTokens?.access,
    gcTime: 5 * 60 * 1000, // Cache for 5 minutes
    refetchOnMount: true,
    refetchOnWindowFocus: true
  });

  // Update observations state when data changes
  useEffect(() => {
    if (obsData) {
      setObservations(obsData as Observation[]);
    }
  }, [obsData]);

  const handleBack = () => {
    if (!deviceId || !dataFileId) return;
    navigate({ to: "/devices/$deviceId/$dataFileId", params: { deviceId, dataFileId } });
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
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>Species</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Amplitude</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {observations.map((observation) => (
              <TableRow key={observation.id}>
                <TableCell>{new Date(observation.obs_dt).toLocaleString()}</TableCell>
                <TableCell>
                  {observation.taxon.species_common_name || observation.taxon.species_name}
                </TableCell>
                <TableCell>{observation.source}</TableCell>
                <TableCell>
                  <span className={`px-2 py-1 rounded ${
                    observation.needs_review ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                  }`}>
                    {observation.needs_review ? 'Needs Review' : 'Reviewed'}
                  </span>
                </TableCell>
                <TableCell>{formatTime(observation.extra_data.duration)}</TableCell>
                <TableCell>{observation.extra_data.avg_amplitude.toFixed(2)}</TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    {deviceId && dataFileId && dataFile && (
                      <>
                        <AudioPlayer
                          deviceId={deviceId}
                          fileId={dataFileId}
                          fileFormat={dataFile.file_format}
                        />
                        <AudioWaveformPlayer
                          deviceId={deviceId}
                          fileId={dataFileId}
                          fileFormat={dataFile.file_format}
                          startTime={observation.extra_data.start_time}
                          endTime={observation.extra_data.end_time}
                        />
                      </>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
} 