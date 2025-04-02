import React from 'react';
import AuthContext from '@/auth/AuthContext'
import { getData, postData } from '@/utils/FetchFunctions'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useContext } from 'react'
import AudioQualityCard from '@/components/AudioQuality/AudioQualityCard'
import { formatFileSize } from '@/utils/formatters'
import type { DataFile } from '@/types'

export const Route = createFileRoute('/devices/$deviceId/$dataFileId')({
  component: RouteComponent,
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
})

function RouteComponent() {
  const { deviceId, dataFileId } = Route.useParams()
  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };
  const queryClient = useQueryClient();

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const apiURL = `devices/${deviceId}/datafiles/${dataFileId}`;

  const getDataFunc = async () => {
    if (!authTokens?.access) return null;
    const responseJson = await getData(apiURL, authTokens.access);
    return {
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
      extraData: responseJson.extra_data,
      thumbUrl: responseJson.thumb_url,
      localStorage: responseJson.local_storage,
      archived: responseJson.archived,
      favourite: responseJson.is_favourite
    };
  };

  const {
    data: dataFile,
    isLoading,
    error,
  } = useQuery({
    queryKey: [apiURL],
    queryFn: getDataFunc,
    enabled: !!authTokens?.access,
  });

  const checkQualityMutation = useMutation({
    mutationFn: async () => {
      if (!authTokens?.access) throw new Error('No auth token');
      return postData(`datafile/${dataFileId}/check_quality/`, authTokens.access, {});
    },
    onSuccess: () => {
      // Refetch the data file to get updated quality information
      queryClient.invalidateQueries({ queryKey: [apiURL] });
    },
  });

  const handleCheckQuality = () => {
    checkQualityMutation.mutate();
  };

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
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">{dataFile.fileName}</h2>
        {dataFile.archived && (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-sm">
            Archived
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* File Information */}
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-lg font-semibold">File Information</h3>
          <div className="space-y-2">
            <div className="text-sm">
              <span className="font-semibold">Format:</span> {dataFile.fileFormat}
            </div>
            <div className="text-sm">
              <span className="font-semibold">Size:</span> {formatFileSize(dataFile.fileSize)}
            </div>
            <div className="text-sm">
              <span className="font-semibold">Recording Date:</span>{' '}
              {dataFile.recordingDt ? new Date(dataFile.recordingDt).toLocaleString() : 'Not available'}
            </div>
            <div className="text-sm">
              <span className="font-semibold">Upload Date:</span>{' '}
              {new Date(dataFile.uploadDt).toLocaleString()}
            </div>
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
          onCheckQuality={handleCheckQuality}
        />
      </div>
    </div>
  );
}
export default Route
