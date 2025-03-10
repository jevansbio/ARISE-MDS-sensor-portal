import React from "react";
import { useContext } from "react";
import AuthContext from "../context/AuthContext";
import { getData } from "../utils/FetchFunctions.js";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import Loading from "../components/Loading.tsx";
import DeploymentMap from "../components/DeploymentMap.tsx";

const HomePage = () => {
	const { authTokens, user } = useContext(AuthContext);

	const getDataFunc = async () => {
		let apiURL = `${"deployment"}/`;
		console.log(apiURL);
		let response_json = await getData(apiURL, authTokens.access);
		return response_json;
	};

	const {
		isLoading,
		isError,
		isPending,
		data,
		error,
		isRefetching,
		isPlaceholderData,
		refetch,
	} = useQuery({
		queryKey: ["deploymentdata", user],
		queryFn: () => getDataFunc(),
		refetchOnWindowFocus: false,
		placeholderData: keepPreviousData,
	});

	if ((isLoading || isPending || isRefetching) & !isPlaceholderData) {
		return <Loading />;
	}
	return <DeploymentMap deployments={data} />;
};

export default HomePage;
