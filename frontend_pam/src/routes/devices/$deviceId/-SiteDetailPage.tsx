import { useQuery } from "@tanstack/react-query";
import { Route } from ".";
import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { useContext } from "react";
import { bytesToMegabytes } from "@/utils/convertion";

export default function DeviceDetailPage() {
  const { deviceId } = Route.useParams();

  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const apiURL = `devices/${deviceId}`;

  const getDeviceFunc = async () => {
    if (!authTokens?.access) return null;

    const responseJson = await getData(apiURL, authTokens.access);

    return responseJson;
  };

  const {
    data: device,
    isLoading,
    error,
  } = useQuery({
    queryKey: [apiURL],
    queryFn: getDeviceFunc,
    enabled: !!authTokens?.access,
  });

  if (isLoading) {
    return <p>Loading device...</p>;
  }
  if (error) {
    return <p>Error: {(error as Error).message}</p>;
  }
  if (!device) {
    return <p>No device found</p>;
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Device Details</h2>
      <div className="grid grid-cols-2 gap-x-8 gap-y-4">
        <p>
          <strong>Device ID:</strong> {device.device_ID}
        </p>
        <p>
          <strong>Deployment ID:</strong> {device.deployment_device_ID}
        </p>
        <p>
          <strong>Start date:</strong> {device.start_date}
        </p>
        <p>
          <strong>End date:</strong> {device.endDate}
        </p>
        <p>
          <strong>Last upload:</strong> {device.lastUpload}
        </p>
        <p>
          <strong>Folder size:</strong> {bytesToMegabytes(device.folder_size)}
        </p>
        <p>
          <strong>Country:</strong> {device.country}
        </p>
        <p>
          <strong>Site:</strong> {device.site_name}
        </p>
        <p>
          <strong>Latitude:</strong> {device.latitude}
        </p>
        <p>
          <strong>Longitude:</strong> {device.longitude}
        </p>
        <p>
          <strong>Coordinate Uncertainty:</strong>{" "}
          {device.coordinate_uncertainty}
        </p>
        <p>
          <strong>GPS device:</strong> {device.gps_device}
        </p>
        <p>
          <strong>Microphone Height:</strong> {device.mic_height}
        </p>
        <p>
          <strong>Microphone Direction:</strong> {device.mic_direction}
        </p>
        <p>
          <strong>Habitat:</strong> {device.habitat}
        </p>
        <p>
          <strong>Score:</strong> {device.score}
        </p>
        <p>
          <strong>Protocol Checklist:</strong> {device.protocol_checklist}
        </p>
        <p>
          <strong>Adresse e-mail:</strong> {device.user_email}
        </p>
        <p>
          <strong>Comment:</strong> {device.comment}
        </p>
      </div>
    </div>
  );
}
