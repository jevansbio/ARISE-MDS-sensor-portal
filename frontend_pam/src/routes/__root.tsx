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
