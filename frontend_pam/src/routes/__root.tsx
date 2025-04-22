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

type User = {
  id: string;
  email: string;
  username: string;
  is_staff?: boolean;
  is_superuser?: boolean;
};

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
}>()({
  component: AuthWrapper,
  errorComponent: ({ error }) => {
    console.error('Router error:', error);
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="p-8 bg-white rounded-lg shadow-lg">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-700">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  },
});

function AuthWrapper() {
  return (
    <AuthProvider>
      <RootComponent />
    </AuthProvider>
  );
}

function RootComponent() {
  const { user } = useContext(AuthContext) as { user: User | null };
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
