import AuthContext from "@/auth/AuthContext";
import DeploymentMap from "@/components/map/DeploymentMap";
import { getData } from "@/utils/FetchFunctions";
import {  useQuery } from "@tanstack/react-query";
import { useContext } from "react";
import { Route } from "./index";
import { Deployment } from "@/types";

type AuthContextType = {
    user: any;
    authTokens: any;
  };

export default function DeploymentMapPage() {
    const { siteName } = Route.useParams();

  const authContext = useContext(AuthContext) as AuthContextType;
  const { authTokens } = authContext || { authTokens: null };

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }
  const apiURL = `deployment/by_site/${siteName}/`;

  const getDataFunc = async (): Promise<Deployment> => {
    if (!authTokens?.access) {
			throw new Error("No access token");
		}
					
    const response_json = await getData(apiURL, authTokens.access);
		console.log("respone_json site deployment map: ", response_json);

    const deployment: Deployment = {
			deploymentId: response_json.deployment_ID,
			startDate: response_json.deployment_start,
			endDate: response_json.deployment_end,
			folderSize: response_json.folder_size,
			lastUpload: response_json.last_upload,
			batteryLevel: 0,
			action: "",
			siteName: response_json.site_name,
			coordinateUncertainty: response_json.coordinate_uncertainty,
			gpsDevice: response_json.gps_device,
			micHeight: response_json.mic_height,
			micDirection: response_json.mic_direction,
			habitat: response_json.habitat,
			protocolChecklist: response_json.protocol_checklist,
			score: response_json.score,
			comment: response_json.comment,
			userEmail: response_json.user_email,
			country: response_json.country,
			longitude: response_json.longitude,
			latitude: response_json.latitude,
		}
    return deployment;
  };

  const {
    data: deployment,
    isLoading,
    error,
  } = useQuery({
    queryKey: [apiURL],
    queryFn: getDataFunc,
    enabled: !!authTokens?.access,
  });

  if (isLoading) {
    return <p>Loading device...</p>;
  }
  if (error) {
    return <p>Error: {(error as Error).message}</p>;
  }

  const deploymentArray = deployment ? [deployment] : [];

	console.log("deploymentArray: ", deploymentArray);

	return (
		<DeploymentMap deployments={deploymentArray} />
	);
}