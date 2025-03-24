import Breadcrumbs from "@/components/Breadcrumbs";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import {
  createRootRouteWithContext,
  Outlet,
  useLocation,
} from "@tanstack/react-router";
import { QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "@/auth/AuthContext";
import { useContext } from "react";
import AuthContext from "@/auth/AuthContext";

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
  //to get around typescript error, we are mixing javascript and typescript to keep original functionality
  const { user } = useContext(AuthContext) as { user: any };
  const { pathname } = useLocation();

  // If there is no authenticated user, only render the Outlet.
  if (!user) {
    return <Outlet />;
  }

  // Optionally hide breadcrumbs on the root path "/"
  const showBreadcrumbs = pathname !== "/";

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
