import AuthContext from '@/auth/AuthContext';
import { getData } from '@/utils/FetchFunctions';
import { useQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router'
import { useContext } from 'react';

export const Route = createFileRoute('/call')({
  component: RouteComponent,
})

function RouteComponent() {
    const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };

  const apiURL = "datafile/";
  const valueKey = "id";
  const labelKey = "name";
  const choices: any[] = [];

  const getDataFunc = async () => {
    console.log("getDataFunc called, authToken:", authTokens?.access);
    let response_json = await getData(apiURL, authTokens.access);
    console.log("Raw API response:", response_json);
    let newOptions = response_json.map((x: any) => {
      return { value: x[valueKey], label: x[labelKey] };
    });
    let allOptions = choices.concat(newOptions);
    console.log("Transformed options:", allOptions);
    return allOptions;
  };

  const { data, isLoading, error } = useQuery({
    queryKey: [apiURL],
    queryFn: getDataFunc,
    enabled: !!authTokens,
  });

  console.log("Query loading:", isLoading);
  console.log("Query error:", error);
  console.log("Query data:", data);
  return <div>Hello "/call"!</div>
}
