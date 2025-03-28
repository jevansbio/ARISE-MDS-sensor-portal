import AuthContext from '@/auth/AuthContext'
import { getData } from '@/utils/FetchFunctions'
import { useQuery } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useContext } from 'react'

export const Route = createFileRoute('/devices/$deviceId/$dataFileId')({
  component: RouteComponent,
})

function RouteComponent() {
  const { deviceId, dataFileId } = Route.useParams()
  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const apiURL = `devices/${deviceId}/datafiles/${dataFileId}`;

  const getDataFunc = async () => {
    if (!authTokens?.access) return null;

    const responseJson = await getData(apiURL, authTokens.access);

    return responseJson;
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
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Audio File Details</h2>
      <div className="space-y-2">
        <p>
          <strong>ID:</strong> {dataFile.id}
        </p>
        <p>
          <strong>Config:</strong> {dataFile.config}
        </p>
        <p>
          <strong>Sample Rate:</strong> {dataFile.samplerate} Hz
        </p>
        <p>
          <strong>File Length:</strong> {dataFile.file_length}
        </p>
        <p>
          <strong>File Size:</strong> {dataFile.file_size} MB
        </p>
        <p>
          <strong>File Format:</strong> {dataFile.file_format}
        </p>
      </div>
    </div>
  )
}
export default Route
