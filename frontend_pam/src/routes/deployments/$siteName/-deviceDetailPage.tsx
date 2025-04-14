import { useQuery } from "@tanstack/react-query";
import { Route } from ".";
import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { useContext } from "react";

export default function DeviceDetailPage() {
  const { siteName } = Route.useParams();
  const authContext = useContext(AuthContext) as { authTokens: { access: string } | null };
  const { authTokens } = authContext || { authTokens: null };

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const apiURL = `devices/by_site/${siteName}/`;

  // Definer et fallback-objekt med tomme felter
  const fallbackDevice = {
    device_ID: "",
    configuration: "",
    sim_card_icc: "",
    sim_card_batch: "",
    sd_card_size: ""
  };

  const getDeviceFunc = async () => {
    if (!authTokens?.access) return null;
    const responseJson = await getData(apiURL, authTokens.access);
    console.log(responseJson);
    return responseJson;
  };

  const { data: device, isLoading, error } = useQuery({
    queryKey: [apiURL],
    queryFn: getDeviceFunc,
    enabled: !!authTokens?.access,
    retry: false // Ikke prøv å gjenta fetch hvis det feiler
  });

  if (isLoading) {
    return <p>Loading device...</p>;
  }

  // I stedet for å vise en feilmelding dersom ingen device er funnet, bruker vi fallbackDevice.
  const displayDevice = device || fallbackDevice;

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Device Details</h2>
      <div className="grid grid-cols-1 gap-4">
        <p>
          <strong>Device ID:</strong> {displayDevice.device_ID}
        </p>
        <p>
          <strong>Configuration:</strong> {displayDevice.configuration}
        </p>
        <p>
          <strong>SIM Card ICC:</strong> {displayDevice.sim_card_icc}
        </p>
        <p>
          <strong>SIM Card Batch:</strong> {displayDevice.sim_card_batch}
        </p>
        <p>
          <strong>SD Card Size (GB):</strong> {displayDevice.sd_card_size}
        </p>
      </div>
    </div>
  );
}
