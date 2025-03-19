import Breadcrumbs from "@/components/Breadcrumbs";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import {
  createRootRouteWithContext,
  Outlet,
  useLocation,
} from "@tanstack/react-router";
import { QueryClient, useQuery } from "@tanstack/react-query";
import AuthContext, { AuthProvider } from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { useContext } from "react";

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
}>()({
  component: AuthWrapper,
});

function AuthWrapper() {
  return (
    <AuthProvider>
      <RootComponent />
    </AuthProvider>
  );
}

function RootComponent() {
  const { pathname } = useLocation();
  // Hide breadcrumbs on the root path "/"
  const showBreadcrumbs = pathname !== "/";

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


  return (
    <div className="flex flex-col">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <div className="flex-1">
          {showBreadcrumbs && <Breadcrumbs />}
          <Outlet />
        </div>
      </div>
    </div>
  );
}
