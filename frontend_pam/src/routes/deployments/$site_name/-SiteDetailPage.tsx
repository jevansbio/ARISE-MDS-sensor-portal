//import { useParams } from "@tanstack/react-router";
import { bytesToMegabytes } from "@/utils/convertion";
import { Route } from "./index";
import AuthContext from "@/auth/AuthContext";
import { useContext } from "react";
import { getData } from "@/utils/FetchFunctions";
import { useQuery } from "@tanstack/react-query";
import { Deployment } from "@/types";

export default function SiteDetailPage() {
  const { site_name } = Route.useParams();

  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }
  const apiURL = `deployment/by_site/${site_name}/`;

  const getDataFunc = async (): Promise<Deployment[]> => {
    if (!authTokens?.access) return [];
    const response_json = await getData(apiURL, authTokens.access);
  
    const deployments: Deployment[] = response_json.map((deployment: any): Deployment => ({
      deploymentId: deployment.Deployment_ID,
      startDate: deployment.start_date,
      endDate: deployment.end_date,
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
      longitude: deployment.longitue,
      latitude: deployment.latidute

    }));
    console.log(deployments)
    return deployments;
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
  if (!deployment) {
    return <p>No device found</p>;
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Device Details</h2>
      {deployment.map((item) => (
        <div key={item.deploymentId} className="grid grid-cols-2 gap-x-8 gap-y-4 mb-6">
          <p>
            <strong>Deployment ID:</strong> {item.deploymentId}
          </p>
          <p>
            <strong>Start Date:</strong> {item.startDate}
          </p>
          <p>
            <strong>End Date:</strong> {item.endDate}
          </p>
          <p>
            <strong>Last Upload:</strong> {item.lastUpload}
          </p>
          <p>
            <strong>Folder Size:</strong>{" "}
            {bytesToMegabytes(item.folder_size)}
          </p>
          <p>
            <strong>Country:</strong> {item.country}
          </p>
          <p>
            <strong>Site Name:</strong> {item.site_name}
          </p>
          <p>
            <strong>Latitude:</strong> {item.latitude}
          </p>
          <p>
            <strong>Longitude:</strong> {item.longitude}
          </p>
          <p>
            <strong>Coordinate Uncertainty:</strong>{" "}
            {item.coordinate_uncertainty}
          </p>
          <p>
            <strong>GPS Device:</strong> {item.gps_device}
          </p>
          <p>
            <strong>Microphone Height:</strong> {item.mic_height}
          </p>
          <p>
            <strong>Microphone Direction:</strong>{" "}
            {item.mic_direction}
          </p>
          <p>
            <strong>Habitat:</strong> {item.habitat}
          </p>
          <p>
            <strong>Score:</strong> {item.score}
          </p>
          <p>
            <strong>Protocol Checklist:</strong> {item.protocol_checklist}
          </p>
          <p>
            <strong>User e-mail:</strong> {item.user_email}
          </p>
          <p>
            <strong>Comment:</strong> {item.comment}
          </p>
        </div>
      ))}
    </div>
  );
}
