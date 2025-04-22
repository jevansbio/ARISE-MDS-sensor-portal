//import { useParams } from "@tanstack/react-router";
import { bytesToMegabytes } from "@/utils/convertion";
import { Route } from "./index";
import AuthContext from "@/auth/AuthContext";
import { useContext } from "react";
import { getData } from "@/utils/FetchFunctions";
import { useQuery } from "@tanstack/react-query";
import { Deployment } from "@/types";
import { timeSinceLastUpload } from "@/utils/timeFormat";

interface AuthContextType {
  authTokens: {
    access: string;
  } | null;
}

interface ApiDeployment {
  deployment_ID: string;
  deployment_start: string;
  deployment_end: string | null;
  folder_size: number;
  last_upload: string;
  site_name: string;
  coordinate_uncertainty: string;
  gps_device: string;
  mic_height: string;
  mic_direction: string;
  habitat: string;
  protocol_checklist: string;
  comment: string;
  user_email: string;
  country: string;
  longitude: number;
  latitude: number;
  score: number;
}

export default function SiteDetailPage() {
  const { siteName } = Route.useParams();

  const authContext = useContext(AuthContext) as AuthContextType;
  const { authTokens } = authContext || { authTokens: null };
  const apiURL = `deployment/by_site/${siteName}/`;

  const getDataFunc = async (): Promise<Deployment> => {
    if (!authTokens?.access) {
      throw new Error("No access token");
    }
          
    const response_json = await getData<ApiDeployment>(apiURL, authTokens.access);
    console.log("respone_json site deployment map: ", response_json);

    const deployment: Deployment = {
      deploymentId: response_json.deployment_ID,
      startDate: response_json.deployment_start,
      endDate: response_json.deployment_end || "",
      folderSize: response_json.folder_size,
      lastUpload: response_json.last_upload,
      batteryLevel: 0,
      action: "",
      siteName: response_json.site_name,
      coordinateUncertainty: response_json.coordinate_uncertainty,
      gpsDevice: response_json.gps_device,
      micHeight: parseFloat(response_json.mic_height) || 0,
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

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

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
          className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6 max-w-3xl"
        >
          <p>
            <strong>Deployment ID:</strong> {deployment.deploymentId}
          </p>
          <p>
            <strong>Start Date:</strong> {deployment.startDate}
          </p>
          <p>
            <strong>End Date:</strong> {deployment.endDate}
          </p>
          <p>
            <strong>Last Upload:</strong> {timeSinceLastUpload(deployment.lastUpload)}
          </p>
          <p>
            <strong>Folder Size:</strong> {bytesToMegabytes(deployment.folderSize)}
          </p>
          <p>
            <strong>Country:</strong> {deployment.country}
          </p>
          <p>
            <strong>Site Name:</strong> {deployment.siteName}
          </p>
          <p>
            <strong>Latitude:</strong> {deployment.latitude}
          </p>
          <p>
            <strong>Longitude:</strong> {deployment.longitude}
          </p>
          <p>
            <strong>Coordinate Uncertainty:</strong>{" "}
            {deployment.coordinateUncertainty}
          </p>
          <p>
            <strong>GPS Device:</strong> {deployment.gpsDevice}
          </p>
          <p>
            <strong>Microphone Height:</strong> {deployment.micHeight}
          </p>
          <p>
            <strong>Microphone Direction:</strong> {deployment.micDirection}
          </p>
          <p>
            <strong>Habitat:</strong> {deployment.habitat}
          </p>
          <p>
            <strong>Score:</strong> {deployment.score}
          </p>
          <p>
            <strong>Protocol Checklist:</strong> {deployment.protocolChecklist}
          </p>
          <p>
            <strong>User e-mail:</strong> {deployment.userEmail}
          </p>
          <p>
            <strong>Comment:</strong> {deployment.comment}
          </p>
        </div>
    </div>
  );
}
