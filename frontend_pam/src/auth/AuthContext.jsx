import React, { createContext, useState } from "react";
import { jwtDecode } from "jwt-decode";

// Use TanStack Router's useNavigate instead of react-router-dom
import { useNavigate } from "@tanstack/react-router";
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

  const loginUserFunction = async (username, password) => {
    console.log("bar");
    const response = await fetch(
      `/${process.env.REACT_APP_API_BASE_URL}/token/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: username, password: password }),
      }
    );
    let data = await response.json();
    if (data) {
      localStorage.setItem("authTokens", JSON.stringify(data));
      setAuthTokens(data);
      setUser(jwtDecode(data.access));
      // Use TanStack Router's navigate – ensure "/" exists in your route tree
      navigate({ to: "/" });
    } else {
      alert("Something went wrong while logging in the user!");
    }
    return data;
  };

  const doLogIn = useMutation({
    mutationFn: ({ username, password }) =>
      loginUserFunction(username, password),
  });

  let loginUser = async (e) => {
    e.preventDefault();
    console.log("foo");
    doLogIn.mutate({
      username: e.target.username.value,
      password: e.target.password.value,
    });
  };

  const updateToken = async () => {
    const response = await fetch(
      `/${process.env.REACT_APP_API_BASE_URL}/token/refresh/`,
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
