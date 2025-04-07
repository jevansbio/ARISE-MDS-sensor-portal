import { useQuery } from "@tanstack/react-query";
import { Route } from ".";
import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { useContext } from "react";

export default function DeviceDetailPage() {
  const { site_name } = Route.useParams();
  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const apiURL = `devices/by_site/${site_name}/`;

  const getDeviceFunc = async () => {
    if (!authTokens?.access) return null;
    const responseJson = await getData(apiURL, authTokens.access);
    console.log(responseJson)
    return responseJson;
  };

  const { data: device, isLoading, error } = useQuery({
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
      <div className="grid grid-cols-1 gap-4">
        <p>
          <strong>Device ID:</strong> {device.device_ID}
        </p>
        <p>
          <strong>Configuration:</strong> {device.configuration}
        </p>
        <p>
          <strong>SIM Card ICC:</strong> {device.sim_card_icc}
        </p>
        <p>
          <strong>SIM Card Batch:</strong> {device.sim_card_batch}
        </p>
        <p>
          <strong>SD Card Size (GB):</strong> {device.sd_card_size}
        </p>
      </div>
    </div>
  );
}
