import AuthContext from '@/auth/AuthContext';
import DeploymentMap from '@/components/map/DeploymentMap';
import { getData } from '@/utils/FetchFunctions';
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

	const getDataFunc = async () => {
		let apiURL = `${"deployment"}/`;
		console.log(apiURL);
		let response_json = await getData(apiURL, authTokens.access);
		return response_json;
	};

  const {
		isLoading,
		isPending,
		data,
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

  return (
    <DeploymentMap deployments={data} />
  );
}