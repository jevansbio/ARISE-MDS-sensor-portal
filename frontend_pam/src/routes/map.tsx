import AuthContext from '@/auth/AuthContext';
import DeploymentMap from '@/components/map/DeploymentMap';
import { Deployment } from '@/types';
import { getData } from '@/utils/FetchFunctions';
import { timeSinceLastUpload } from '@/utils/timeFormat';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
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
  const { authTokens, user } = useContext(AuthContext) as AuthContextType;

  const apiURL = "deployment/";

  const getDataFunc = async (): Promise<Deployment[]> => {
    if (!authTokens?.access) return [];
    const response_json = await getData(apiURL, authTokens.access);
  
    const deployments: Deployment[] = response_json.map((deployment: any): Deployment => ({
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
      score: deployment,
      comment: deployment.comment,
      user_email: deployment.user_email,
      country: deployment.country,
      longitude: deployment.longitude,
      latitude: deployment.latitude
    }));
    console.log(deployments)
    return deployments;
  };

  const {
		isLoading,
		isPending,
		data: deployments,
		error,
		isRefetching,
		isPlaceholderData,
	} = useQuery({
		queryKey: ["deploymentdata", user],
		queryFn: () => getDataFunc(),
		refetchOnWindowFocus: false,
		placeholderData: keepPreviousData,
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