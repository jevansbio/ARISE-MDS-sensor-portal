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

  const getDataFunc = async () => {
    if (!authTokens?.access) return null;
    const responseJson = await getData(apiURL, authTokens.access);
    console.log(responseJson)
    return responseJson;
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
    return <p>Loading deployment...</p>;
  }
  if (error) {
    return <p>Error: {(error as Error).message}</p>;
  }
  if (!deployment) {
    return <p>No deployment found</p>;
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Site Details</h2>
        <div
          key={deployment.deploymentId}
          className="grid grid-cols-2 gap-x-8 gap-y-4 mb-6"
        >
          <p>
            <strong>Deployment ID:</strong> {deployment.deployment_ID}
          </p>
          <p>
            <strong>Start Date:</strong> {deployment.deployment_start}
          </p>
          <p>
            <strong>End Date:</strong> {deployment.deployment_end}
          </p>
          <p>
            <strong>Last Upload:</strong> {deployment.lastUpload}
          </p>
          <p>
            <strong>Folder Size:</strong> {bytesToMegabytes(deployment.folder_size)}
          </p>
          <p>
            <strong>Country:</strong> {deployment.country}
          </p>
          <p>
            <strong>Site Name:</strong> {deployment.site_name}
          </p>
          <p>
            <strong>Latitude:</strong> {deployment.latitude}
          </p>
          <p>
            <strong>Longitude:</strong> {deployment.longitude}
          </p>
          <p>
            <strong>Coordinate Uncertainty:</strong>{" "}
            {deployment.coordinate_uncertainty}
          </p>
          <p>
            <strong>GPS Device:</strong> {deployment.gps_device}
          </p>
          <p>
            <strong>Microphone Height:</strong> {deployment.mic_height}
          </p>
          <p>
            <strong>Microphone Direction:</strong> {deployment.mic_direction}
          </p>
          <p>
            <strong>Habitat:</strong> {deployment.habitat}
          </p>
          <p>
            <strong>Score:</strong> {deployment.score}
          </p>
          <p>
            <strong>Protocol Checklist:</strong> {deployment.protocol_checklist}
          </p>
          <p>
            <strong>User e-mail:</strong> {deployment.user_email}
          </p>
          <p>
            <strong>Comment:</strong> {deployment.comment}
          </p>
        </div>
    </div>
  );
}
