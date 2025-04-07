import AuthContext from "@/auth/AuthContext";
import DeploymentMap from "@/components/map/DeploymentMap";
import { getData } from "@/utils/FetchFunctions";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useContext } from "react";
import { Route } from "./index";
import { Deployment } from "@/types";

type AuthContextType = {
    user: any;
    authTokens: any;
  };

export default function DeploymentMapPage() {
    const { site_name } = Route.useParams();

  const authContext = useContext(AuthContext) as AuthContextType;
  const { authTokens } = authContext || { authTokens: null };

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }
  const apiURL = `deployment/by_site/${site_name}/`;

  const getDataFunc = async (): Promise<Deployment> => {
    if (!authTokens?.access) {
			throw new Error("No access token");
		}
					
    const response_json = await getData(apiURL, authTokens.access);

    const deployment: Deployment = response_json.map(
      (deployment: any): Deployment => ({
        deploymentId: deployment.deployment_ID,
        startDate: deployment.deployment_start,
        endDate: deployment.deployment_end,
        folder_size: deployment.folder_size,
        lastUpload: deployment.last_upload,
        batteryLevel: 0,
        action: "",
        site_name: deployment.site_name,
        dataFile: [],
        coordinate_uncertainty: deployment.coordinate_uncertainty,
        gps_device: deployment.gps_device,
        mic_height: deployment.mic_height,
        mic_direction: deployment.mic_direction,
        habitat: deployment.habitat,
        protocol_checklist: deployment.protocol_checklist,
        score: deployment.score,
        comment: deployment.comment,
        user_email: deployment.user_email,
        country: deployment.country,
        longitude: deployment.longitude,
        latitude: deployment.latitude,
      })
    );
    console.log("Deployment: ", deployment);
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

  console.log(deployment);

  if (isLoading) {
    return <p>Loading device...</p>;
  }
  if (error) {
    return <p>Error: {(error as Error).message}</p>;
  }

  const deploymentArray = deployment ? [deployment] : [];

	return (
		<DeploymentMap deployments={deploymentArray} />
	);
}