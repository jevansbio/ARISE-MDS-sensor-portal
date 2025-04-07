import AuthContext from "@/auth/AuthContext";
import DeploymentMap from "@/components/map/DeploymentMap";
import { getData } from "@/utils/FetchFunctions";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useContext } from "react";
import { Route } from "./index";

type AuthContextType = {
    user: any;
    authTokens: any;
  };

export default function DeploymentMapPage() {
    const { deviceId } = Route.useParams(); //change to deployment when the names and routing have changed

    const { authTokens, user } = useContext(AuthContext) as AuthContextType;

	const getDataFunc = async () => {
		let apiURL = `deployment/${deploymentId}`;
		console.log(apiURL);
		let response_json = await getData(apiURL, authTokens.access);
		return response_json;
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

    return (
        <DeploymentMap deployments={deployments} />
      );


}