// src/ProtectedRoute.js
import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import AuthContext from "../context/AuthContext";
import { useContext } from "react";

const ProtectedRoute = () => {
	let { user } = useContext(AuthContext);
	if (!user) {
		return (
			<Navigate
				to="/login"
				replace
			/>
		);
	}

	return <Outlet />;
};

export default ProtectedRoute;
