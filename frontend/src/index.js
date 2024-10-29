import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
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
					{ path: "/deployments", element: <Gallery /> },
					{
						path: "/devices",
						element: (
							<Gallery
								objectType={"device"}
								nameKey={"deviceID"}
							/>
						),
					},
					{
						path: "/projects",

						children: [
							{
								path: "",
								element: (
									<Gallery
										objectType={"project"}
										nameKey={"projectID"}
									/>
								),
							},
							{
								path: ":id",
								element: (
									<DetailPage
										objectType="project"
										nameKey={"projectID"}
									/>
								),
							},
						],
					},
					{
						path: "/datafiles",
						element: (
							<Gallery
								objectType={"datafile"}
								nameKey={"file_name"}
							/>
						),
					},
				],
			},
			{ path: "/login", element: <LoginPage />, children: [] },
			{
				path: "*",
				element: <p>404 Error - Nothing here...</p>,
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
