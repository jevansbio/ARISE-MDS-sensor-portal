import React, { createContext, useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";

// Use TanStack Router's useNavigate instead of react-router-dom
import { useNavigate, useLocation } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";

const AuthContext = createContext();

//Made as similiar as possible to this: https://github.com/jevansbio/ARISE-MDS-sensor-portal/blob/Testing/frontend/src/context/AuthContext.jsx

// Export AuthContext so it can be imported and used by other modules
export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;

export const AuthProvider = ({ children }) => {
  // Initialize the user state by checking if auth tokens exist in localStorage
  // If tokens exist, decode them to set the user state; otherwise, set to null
  const [user, setUser] = useState(() =>
    sessionStorage.getItem("authTokens")
      ? jwtDecode(sessionStorage.getItem("authTokens"))
      : null
  );
  console.log("User:", user);
  // Initialize authTokens state by parsing the tokens from localStorage if they exist
  const [authTokens, setAuthTokens] = useState(() =>
    sessionStorage.getItem("authTokens")
      ? JSON.parse(sessionStorage.getItem("authTokens"))
      : null
  );
  console.log("AuthTokens:", authTokens);
  const navigate = useNavigate();
  const location = useLocation();


  // Check authentication status on start or when the user state changes.
  // If the user is not authenticated and not on the login page, redirect to "/login".
  useEffect(() => {
    if (!user && location.pathname !== "/login") {
      navigate({ to: "/login" });
    }
  }, [user, location.pathname, navigate]);

  const loginUserFunction = async (username, password) => {
    console.log("bar");
    console.log("Inside loginUserFunction, trying:", username, password);
  
    try {
       // Log the API endpoint for debugging purposes
      console.log("API URL:", `/${import.meta.env.VITE_API_BASE_URL}/token/`);
      
      // Make a POST request to the token endpoint with the provided credentials
      const response = await fetch(`/${import.meta.env.VITE_API_BASE_URL}/token/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password}),
      });
  
      // Log response status and headers for debugging
      console.log("Response status:", response.status);
      console.log("Response headers:", response.headers);
  
      // If the response is not OK, log the error and alert the user
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server returned error:", errorText);
        alert(`Login failed: ${errorText}`);
        return;
      }
  
       // Parse the JSON response to get the tokens
      let data = await response.json();
      console.log("Received data:", data);
  
      sessionStorage.setItem("authTokens", JSON.stringify(data));
      console.log("Saved tokens:", JSON.parse(sessionStorage.getItem("authTokens")));
  
      // Update authTokens and user state using the new tokens
      setAuthTokens(data);
      setUser(jwtDecode(data.access));
      // Navigate to the home page on successful login
      navigate({ to: "/" });
  
      return data;
  
    } catch (error) {
      console.error("Fetch error:", error);
      alert("Network error: Unable to reach API.");
    }
  };
  const doLogIn = useMutation({
    mutationFn: ({ username, password }) =>
      loginUserFunction(username, password),
  });

  // Event handler for the login form submission.
  let loginUser = async (e) => {
    e.preventDefault();
    console.log("foo");
    console.log("Trying to log in with:", e.target.username.value, e.target.password.value);
    doLogIn.mutate({
      username: e.target.username.value,
      password: e.target.password.value,
    });
  };

  // Function to update the authentication token by refreshing it.
  // It sends a POST request to the token refresh endpoint using the refresh token.
  const updateToken = async () => {
    const response = await fetch(
      `/${import.meta.env.VITE_API_BASE_URL}/token/refresh/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh: authTokens?.refresh }),
      }
    );

    const data = await response.json();
    if (response.status === 200) {
      setAuthTokens(data);
      setUser(jwtDecode(data.access));
      sessionStorage.setItem("authTokens", JSON.stringify(data));
    } else {
      logoutUser();
    }
    return data;
  };

  // Use React Query to automatically refresh the token periodically.
  // The token is refreshed every 4 minutes, and also when the window regains focus.
  useQuery({
    queryKey: [`refreshToken-${user}`],
    queryFn: updateToken,
    enabled: authTokens != null,
    refetchInterval: 1000 * 60 * 4,
    refetchOnWindowFocus: true,
  });

  // Function to handle user logout.
  // It clears localStorage and resets the state, then redirects to the login page.
  let logoutUser = (e) => {
    if (e) {
      e.preventDefault();
    }
    sessionStorage.removeItem("authTokens");
    setAuthTokens(null);
    setUser(null);
    // Navigate to "/login" – ensure this route is defined in your route tree
    navigate({ to: "/login" });
  };

  // Prepare the context data to be provided to all consuming components
  let contextData = {
    user: user,
    authTokens: authTokens,
    loginUser: loginUser,
    logoutUser: logoutUser,
    useAuth: useAuth
  };

  // Removed Header and Outlet; now simply render children so that __root.tsx layout is used.
  return (
    <AuthContext.Provider value={contextData}>
      {children}
    </AuthContext.Provider>
  );
};
