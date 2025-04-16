import AuthContext from '@/auth/AuthContext'
import { getData, postData } from '@/utils/FetchFunctions'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, Outlet, useLocation } from '@tanstack/react-router'
import { useContext, useEffect, useState } from 'react'
import AudioQualityCard from '@/components/AudioQuality/AudioQualityCard'
import { formatFileSize } from '@/utils/formatters'
import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";
import AudioWaveformPlayer from "@/components/AudioWaveformPlayer/AudioWaveformPlayer";
import DownloadButton from "@/components/DownloadButton/DownloadButton";

export interface ExtraData {
  quality_metrics?: Record<string, any>;
  temporal_evolution?: Record<string, any>;
  observations?: string[];
  auto_detected_observations: number[];
}

export interface DataFile {
  id: string;
  deployment: string;
  fileName: string;
  fileFormat: string;
  fileSize: number;
  fileType: string;
  path: string;
  localPath: string;
  uploadDt: string;
  recordingDt: string;
  config: string | null;
  sampleRate: number | null;
  fileLength: string | null;
  qualityScore: number | null;
  qualityIssues: string[];
  qualityCheckDt: string | null;
  qualityCheckStatus: string;
  extraData: ExtraData | null;
  thumbUrl?: string;
  localStorage?: boolean;
  archived?: boolean;
  favourite?: boolean;
}

export const Route = createFileRoute('/deployments/$siteName/$dataFileId')({
  component: RouteComponent,
  beforeLoad: ({ location }) => {
    console.log('Loading data file route, path:', location.pathname);
    return true;
  },
  errorComponent: ({ error }) => {
    console.error('Route error:', error);
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="p-8 bg-white rounded-lg shadow-lg">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-700">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  },
  validateSearch: (search: Record<string, unknown>) => {
    return { 
      observationId: typeof search.observationId === 'string' ? search.observationId : undefined 
    };
  }
})

function RouteComponent() {
  const { siteName, dataFileId } = Route.useParams()
  const { observationId } = Route.useSearch()
  const location = useLocation()
  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };
  const queryClient = useQueryClient();
  const [currentObservation, setCurrentObservation] = useState<any>(null);

  const apiURL = `datafile/${dataFileId}/`;

  const getDataFile = async () => {
    if (!authTokens?.access) return null;
    const responseJson = await getData(apiURL, authTokens.access);
    console.log('Raw API response:', responseJson);
    
    // Transform the response data
    const transformedData: DataFile = {
      id: responseJson.id,
      deployment: responseJson.deployment,
      fileName: responseJson.file_name,
      fileFormat: responseJson.file_format,
      fileSize: responseJson.file_size,
      fileType: responseJson.file_type,
      path: responseJson.path,
      localPath: responseJson.local_path,
      uploadDt: responseJson.upload_dt,
      recordingDt: responseJson.recording_dt,
      config: responseJson.config,
      sampleRate: responseJson.sample_rate,
      fileLength: responseJson.file_length,
      qualityScore: responseJson.quality_score,
      qualityIssues: responseJson.quality_issues || [],
      qualityCheckDt: responseJson.quality_check_dt,
      qualityCheckStatus: responseJson.quality_check_status,
      extraData: null,
      thumbUrl: responseJson.thumb_url,
      localStorage: responseJson.local_storage,
      archived: responseJson.archived,
      favourite: responseJson.is_favourite
    };

    // Handle extra_data separately to ensure proper typing
    if (responseJson.extra_data) {
      transformedData.extraData = {
        quality_metrics: responseJson.extra_data.quality_metrics || {},
        temporal_evolution: responseJson.extra_data.temporal_evolution || {},
        observations: responseJson.extra_data.observations || [],
        auto_detected_observations: responseJson.extra_data.auto_detected_observations || []
      };
    }

    console.log('Transformed data:', transformedData);
    return transformedData;
  };

  const {
    data: dataFile,
    isLoading,
    error,
  } = useQuery({
    queryKey: [apiURL],
    queryFn: getDataFile,
    enabled: !!authTokens?.access,
  });

  const checkQualityMutation = useMutation({
    mutationFn: async () => {
      if (!authTokens?.access) throw new Error('No auth token');
      return postData(`datafile/${dataFileId}/check_quality/`, authTokens.access, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [apiURL] });
    },
  });

  const handleCheckQuality = () => {
    checkQualityMutation.mutate();
  };

  // Query for the specific observation if observationId is provided
  const { data: observation } = useQuery({
    queryKey: ['observation', observationId],
    queryFn: async () => {
      if (!observationId || !authTokens?.access) return null;
      try {
        const data = await getData(`observation/${observationId}/`, authTokens.access);
        return data;
      } catch (error) {
        console.error('Failed to fetch observation:', error);
        return null;
      }
    },
    enabled: !!observationId && !!authTokens?.access
  });

  // Set current observation when it's loaded
  useEffect(() => {
    if (observation) {
      setCurrentObservation(observation);
    }
  }, [observation]);

  // Early returns after all hooks are called
  if (location.pathname.endsWith('/observations')) {
    return (
      <div className="w-full h-full">
        <Outlet />
      </div>
    )
  }

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  if (isLoading) {
    return <p>Loading datafile...</p>;
  }

  if (error) {
    return <p>Error: {(error as Error).message}</p>;
  }

  if (!dataFile) {
    return <p>No datafile found</p>;
  }

  return (
    <div className="container mx-auto py-10">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Data File Details</h1>
        <div className="flex gap-2">
          <DownloadButton
            deviceId={siteName}
            fileId={dataFileId}
            fileFormat={dataFile.fileFormat}
          />
          <Link to="/deployments/$siteName" params={{ siteName }}>
            <Button variant="outline">Back to Deployment</Button>
          </Link>
        </div>
      </div>

      {dataFile.fileFormat.toLowerCase().includes('mp3') && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Audio Preview</h2>
          <AudioWaveformPlayer
            deviceId={siteName}
            fileId={dataFileId}
            fileFormat={dataFile.fileFormat}
            startTime={currentObservation?.extra_data?.start_time}
            endTime={currentObservation?.extra_data?.end_time}
            totalDuration={dataFile.fileLength ? parseFloat(dataFile.fileLength) : undefined}
          />
        </div>
      )}

      {currentObservation && (
        <div className="mb-8 p-4 bg-blue-50 rounded-lg">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Selected Observation</h2>
            <Link 
              to="/deployments/$siteName/$dataFileId/observations"
              params={{ siteName, dataFileId }}
              className="text-blue-600 hover:underline"
            >
              View All Observations
            </Link>
          </div>
          <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span className="font-medium">Species: </span>
              {currentObservation.taxon?.species_name || 'Unknown'} 
              {currentObservation.taxon?.species_common_name ? ` (${currentObservation.taxon.species_common_name})` : ''}
            </div>
            <div>
              <span className="font-medium">Time: </span>
              {currentObservation.extra_data?.start_time ? 
                `${currentObservation.extra_data.start_time.toFixed(2)}s - ${currentObservation.extra_data.end_time.toFixed(2)}s` : 
                'N/A'}
            </div>
            <div>
              <span className="font-medium">Duration: </span>
              {currentObservation.extra_data?.duration ? 
                `${currentObservation.extra_data.duration.toFixed(2)}s` : 
                'N/A'}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">File Information</h2>
          <div className="space-y-2">
            <p><span className="font-medium">File Name:</span> {dataFile.fileName}</p>
            <p><span className="font-medium">File Format:</span> {dataFile.fileFormat}</p>
            <p><span className="font-medium">File Size:</span> {formatFileSize(dataFile.fileSize)}</p>
            <p><span className="font-medium">File Type:</span> {dataFile.fileType}</p>
            <p><span className="font-medium">Sample Rate:</span> {dataFile.sampleRate}</p>
            <p><span className="font-medium">File Length:</span> {dataFile.fileLength}</p>
            <p><span className="font-medium">Quality Score:</span> {dataFile.qualityScore}</p>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Recording Information</h2>
          <div className="space-y-2">
            <p><span className="font-medium">Upload Date:</span> {new Date(dataFile.uploadDt).toLocaleString()}</p>
            <p><span className="font-medium">Recording Date:</span> {new Date(dataFile.recordingDt).toLocaleString()}</p>
            <p><span className="font-medium">Quality Check Date:</span> {dataFile.qualityCheckDt ? new Date(dataFile.qualityCheckDt).toLocaleString() : 'Not checked'}</p>
            <p><span className="font-medium">Quality Check Status:</span> {dataFile.qualityCheckStatus}</p>
          </div>
        </div>
      </div>

      {dataFile.qualityIssues && dataFile.qualityIssues.length > 0 && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold mb-4">Quality Issues</h2>
          <ul className="list-disc list-inside space-y-2">
            {dataFile.qualityIssues.map((issue: string, index: number) => (
              <li key={index}>{issue}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* File Information */}
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-lg font-semibold">File Information</h3>
          <div className="space-y-2">
            <div className="text-sm">
              <span className="font-semibold">Storage:</span>{' '}
              {dataFile.localStorage ? 'Local' : 'Remote'}
            </div>
            {dataFile.extraData && Object.keys(dataFile.extraData).length > 0 && (
              <div className="text-sm">
                <span className="font-semibold">Additional Data:</span>
                <pre className="mt-1 p-2 bg-gray-50 rounded text-xs">
                  {JSON.stringify(dataFile.extraData, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Quality Information */}
        <AudioQualityCard
          dataFile={dataFile}
          deviceId={siteName}
          onCheckQuality={handleCheckQuality}
        />
      </div>
    </div>
  );
}
export default Route
