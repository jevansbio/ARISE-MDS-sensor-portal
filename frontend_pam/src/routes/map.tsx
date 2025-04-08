import AuthContext from '@/auth/AuthContext';
import DeploymentMap from '@/components/map/DeploymentMap';
import { Deployment } from '@/types';
import { getData } from '@/utils/FetchFunctions';
import { useQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router'
import { useContext } from 'react';

type AuthContextType = {
  user: any;
  authTokens: any;
};

export const Route = createFileRoute('/map')({
  component: RouteComponent,
})

function RouteComponent() {
  const { authTokens } = useContext(AuthContext) as AuthContextType;

  const apiURL = "deployment/";

  const getDataFunc = async (): Promise<Deployment[]> => {
    if (!authTokens?.access) return [];
    const response_json = await getData(apiURL, authTokens.access);
  
    const deployments: Deployment[] = response_json.map((deployment: any): Deployment => ({
      deploymentId: deployment.deployment_ID,
      startDate: deployment.deployment_start,
      endDate: deployment.deployment_end,
      folderSize: deployment.folder_size,
      lastUpload: deployment.last_upload,
      batteryLevel: 0,
      action: "",
      siteName: deployment.site_name,
      coordinateUncertainty: deployment.coordinate_uncertainty,
      gpsDevice: deployment.gps_device,
      micHeight: deployment.mic_height,
      micDirection: deployment.mic_direction,
      habitat: deployment.habitat,
      protocolChecklist: deployment.protocol_checklist,
      score: deployment,
      comment: deployment.comment,
      userEmail: deployment.user_email,
      country: deployment.country,
      longitude: deployment.longitude,
      latitude: deployment.latitude
    }));
    console.log("Deployments on map: ", deployments)
    return deployments;
  };

  const {
		data: deployments,
		isLoading,
		error,
	} = useQuery({
		queryKey: [apiURL],
		queryFn: getDataFunc,
	});

  if (isLoading) {
    return <div>Loading data...</div>;
  }

  if (error) {
    return <div>Error occurred: {(error as any).message}</div>;
  }

  console.log("deployments data map 123: ", deployments);
  return (
    <DeploymentMap deployments={deployments ?? []} />
  );
}