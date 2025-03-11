import { audioFileQueryOptions } from '@/api/query'
import { useSuspenseQuery } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/devices/$deviceId/$audioFileId')({
  loader: async ({ params: { deviceId, audioFileId }, context: { queryClient } }) => {
    await queryClient.prefetchQuery(audioFileQueryOptions(deviceId, audioFileId))
    return { deviceId }
  },
  component: RouteComponent,
})

function RouteComponent() {
  const { deviceId, audioFileId } = Route.useParams()
  const { data: audioFile } = useSuspenseQuery(audioFileQueryOptions(deviceId, audioFileId));

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Audio File Details</h2>
      <div className="space-y-2">
        <p>
          <strong>ID:</strong> {audioFile.id}
        </p>
        <p>
          <strong>Config:</strong> {audioFile.config}
        </p>
        <p>
          <strong>Sample Rate:</strong> {audioFile.samplerate} Hz
        </p>
        <p>
          <strong>File Length:</strong> {audioFile.fileLength}
        </p>
        <p>
          <strong>File Size:</strong> {audioFile.fileSize} MB
        </p>
      </div>
    </div>
  )

}
