import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { createBrowserRouter, RouterProvider, Outlet } from "react-router-dom";
import reportWebVitals from "./reportWebVitals";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import { AuthProvider } from "./context/AuthContext";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ProtectedRoute from "./utils/ProtectedRoute.jsx";
import { Toaster } from "react-hot-toast";
import Gallery from "./components/Gallery/Gallery.tsx";
import "bootstrap/dist/css/bootstrap.min.css";
import DetailPage from "./components/Detail/DetailPage.tsx";
import Error404page from "./pages/Error404page.jsx";
import ObjectTypeCheck from "./components/ObjectTypeCheck.tsx";

const queryClient = new QueryClient();

const router = createBrowserRouter([
	{
		element: <AuthProvider />,
		children: [
			{
				element: <ProtectedRoute />,
				children: [{ path: "/", element: <HomePage /> }],
			},
			{
				element: <ProtectedRoute />,
				children: [
					{
						element: <ObjectTypeCheck />,
						children: [
							{
								path: "/:fromObject",
								children: [
									{
										path: "",
										element: <Gallery />,
									},
									{
										path: ":fromID",
										children: [
											{
												path: "",
												element: <DetailPage />,
											},
											{ path: ":objectType", element: <Gallery /> },
										],
									},
								],
							},
						],
					},
				],
			},
			{ path: "/login", element: <LoginPage />, children: [] },
			{
				path: "*",
				element: <Error404page />,
			},
		],
	},
]);

ReactDOM.createRoot(document.getElementById("root")).render(
	<React.StrictMode>
		<Toaster />
		<QueryClientProvider client={queryClient}>
			<RouterProvider router={router} />
		</QueryClientProvider>
	</React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
