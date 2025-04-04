import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useContext } from "react";

export const Route = createFileRoute("/call")({
  component: RouteComponent,
});

function RouteComponent() {
   // Retrieve the authentication context which holds the auth tokens and related functions
  const authContext = useContext(AuthContext) as any;
  console.log("AuthContext value:", authContext);


  // Destructure authTokens from the context. If authContext is undefined, default to { authTokens: null }
  const { authTokens } = authContext || { authTokens: null };
  console.log("AuthContext value:", authContext);

  // If there are no authentication tokens available, display a loading message
  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const apiURL = "devices/10000000d642707c/datafiles/1";

   // Function that fetches data from the API using the stored authentication token
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

      return response_json;
    } catch (error) {
      console.error("API call failed:", error);
      throw error;
    }
  };

  // Use TanStack React Query to manage the API call and its state.
  // The query is enabled only if an access token is available.
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
    </div>
  );
}

export default RouteComponent;
