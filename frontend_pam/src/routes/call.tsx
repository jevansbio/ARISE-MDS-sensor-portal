import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useContext } from "react";

export const Route = createFileRoute("/call")({
  component: RouteComponent,
});

function RouteComponent() {
  const authContext = useContext(AuthContext) as any;
  console.log("AuthContext value:", authContext);

  const { authTokens } = authContext || { authTokens: null };
  console.log("AuthContext value:", authContext);

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const apiURL = "device/";
  const valueKey = "id";
  const labelKey = "name";

  const getDataFunc = async () => {
    console.log("hecking authTokens:", authTokens);
    if (!authTokens?.access) {
      console.warn("Auth token is missing, skipping API call");
      return [];
    }

    console.log("Making API call with token:", authTokens.access);
    try {
      const response_json = await getData(apiURL, authTokens.access);
      console.log("API response:", response_json);

      return response_json.map((x: any) => ({
        value: x[valueKey],
        label: x[labelKey],
      }));
    } catch (error) {
      console.error("API call failed:", error);
      throw error;
    }
  };

  const { data, isLoading, error } = useQuery({
    queryKey: [apiURL],
    queryFn: getDataFunc,
    enabled: !!authTokens?.access, // Spørring starter kun når authTokens er tilgjengelig
  });

  console.log("Query loading:", isLoading);
  console.log("Query error:", error);
  console.log("Query data:", data);

  return (
    <div>
      <h1>Hello "/call"!</h1>
      {isLoading && <p>Loading data...</p>}
      {error && <p>Error fetching data: {error.message}</p>}
      {data && (
        <ul>
          {data.map((item: any) => (
            <li key={item.value}>{item.label}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default RouteComponent;
