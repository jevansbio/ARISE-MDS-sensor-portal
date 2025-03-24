import React, { createContext, useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";

// Use TanStack Router's useNavigate instead of react-router-dom
import { useNavigate, useLocation } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";

const AuthContext = createContext();



export default AuthContext;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() =>
    localStorage.getItem("authTokens")
      ? jwtDecode(localStorage.getItem("authTokens"))
      : null
  );
  const [authTokens, setAuthTokens] = useState(() =>
    localStorage.getItem("authTokens")
      ? JSON.parse(localStorage.getItem("authTokens"))
      : null
  );

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!user && location.pathname !== "/login") {
      navigate({ to: "/login" });
    }
  }, [user, location.pathname, navigate]);

  const loginUserFunction = async (username, password) => {
    console.log("bar");
    console.log("Inside loginUserFunction, trying:", username, password);
  
    try {
      console.log("API URL:", `/${import.meta.env.VITE_API_BASE_URL}/token/`);
      
      const response = await fetch(`/${import.meta.env.VITE_API_BASE_URL}/token/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password}),
      });
  
      console.log("Response status:", response.status);
      console.log("Response headers:", response.headers);
  
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server returned error:", errorText);
        alert(`Login failed: ${errorText}`);
        return;
      }
  
      let data = await response.json();
      console.log("Received data:", data);
  
      localStorage.setItem("authTokens", JSON.stringify(data));
      console.log("Saved tokens:", JSON.parse(localStorage.getItem("authTokens")));
  
      setAuthTokens(data);
      setUser(jwtDecode(data.access));
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

  let loginUser = async (e) => {
    e.preventDefault();
    console.log("foo");
    console.log("Trying to log in with:", e.target.username.value, e.target.password.value);
    doLogIn.mutate({
      username: e.target.username.value,
      password: e.target.password.value,
    });
  };

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
      localStorage.setItem("authTokens", JSON.stringify(data));
    } else {
      logoutUser();
    }
    return data;
  };

  useQuery({
    queryKey: [`refreshToken-${user}`],
    queryFn: updateToken,
    enabled: authTokens != null,
    refetchInterval: 1000 * 60 * 4,
    refetchOnWindowFocus: true,
  });

  let logoutUser = (e) => {
    if (e) {
      e.preventDefault();
    }
    localStorage.removeItem("authTokens");
    setAuthTokens(null);
    setUser(null);
    // Navigate to "/login" – ensure this route is defined in your route tree
    navigate({ to: "/login" });
  };

  let contextData = {
    user: user,
    authTokens: authTokens,
    loginUser: loginUser,
    logoutUser: logoutUser,
  };

  // Removed Header and Outlet; now simply render children so that your __root.tsx layout is used.
  return (
    <AuthContext.Provider value={contextData}>
      {children}
    </AuthContext.Provider>
  );
};
