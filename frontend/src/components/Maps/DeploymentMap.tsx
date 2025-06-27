import React, {
	useCallback,
	useContext,
	useEffect,
	useRef,
	useState,
} from "react";
import {
	FeatureGroup,
	LayerGroup,
	LayersControl,
	MapContainer,
	Popup,
	TileLayer,
} from "react-leaflet";
import UserLocationMarker from "./MapUserLocationMarker.tsx";
import ResetLocation from "./MapControlResetLocation.tsx";

import { Icon } from "leaflet";
import { Marker as CompMarker } from "@adamscybot/react-leaflet-component-marker";
import "../../BeautifyMarker/leaflet-beautify-marker-icon.css";
import AuthContext from "../../context/AuthContext.jsx";
import { getData } from "../../utils/FetchFunctions.js";
import {
	keepPreviousData,
	useInfiniteQuery,
	useQuery,
} from "@tanstack/react-query";
import Loading from "../General/Loading.tsx";
import { Link } from "react-router-dom";

interface Props {
	deployments: [{ latitude; longitude; deployment_device_ID }];
}

interface IconProps {
	borderColor?: string;
	borderStyle?: string;
	backgroundColor?: string;
	textColor?: string;
	borderWidth?: number;
	iconSize?: [number, number];
	symbolSize?: number;
	symbol?: string;
}

const DeploymentMarker = (deployment) => {
	let latLng = {
		lat: deployment.latitude,
		lng: deployment.longitude,
	};

	return (
		<CompMarker
			key={deployment.deployment_device_ID}
			position={latLng}
			icon={
				<DeploymentIcon
					borderColor={deployment.colour}
					textColor="black"
					symbol={deployment.symbol}
				/>
			}
		>
			<Popup>
				{
					<>
						<strong>{deployment.deployment_device_ID}</strong>
						{deployment.thumb_url !== null && deployment.thumb_url !== "" ? (
							<img
								src={"/" + deployment.thumb_url}
								alt={deployment.thumb_url}
							/>
						) : null}
						<ul>
							<li>{deployment.site}</li>
							<li>{deployment.deployment_start}</li>
						</ul>
						<Link
							to={`/deployments/${deployment.id}`}
							className="p-2 flex-fill"
						>
							<button className="btn btn-primary w-100">Open</button>
						</Link>
					</>
				}
			</Popup>
		</CompMarker>
	);
};

const DeploymentIcon = ({
	borderColor = "#1EB300",
	borderStyle = "solid",
	backgroundColor = "white",
	textColor = "#000",
	borderWidth = 2,
	iconSize = [28, 28],
	symbolSize = 16,
	symbol = "",
}: IconProps) => {
	return (
		<div className={"beautify-marker"}>
			<div
				className={"beautify-marker marker"}
				style={{
					borderColor: borderColor,
					borderStyle: borderStyle,
					backgroundColor: backgroundColor,
					borderWidth: borderWidth,
					marginLeft: -iconSize[0] / 2,
					marginTop: -(iconSize[0] / 4 + 1 + iconSize[0]),
					width: iconSize[0],
					height: iconSize[1],
				}}
			>
				<div
					style={{
						height: "100%",
						width: "100%",
					}}
				>
					{symbol !== "" && (
						<img
							src={`https://api.iconify.design/${symbol}.svg`}
							alt={symbol}
						/>
					)}
				</div>
			</div>
		</div>
	);
};

export const DeploymentMapContainer = () => {
	const { authTokens, user } = useContext(AuthContext);
	const [map, setMap] = useState(null);
	const featureGroupRef = useRef();

	const getDataTypesFunc = async () => {
		let apiURL = "datatype/?page_size=100&page=1";
		let response_json = await getData(apiURL, authTokens.access);
		if (!response_json.ok) {
			return [];
		}
		return response_json.results;
	};

	const getDeploymentDataFunc = async ({ pageParam }) => {
		let apiURL = `deployment/?is_active=True&page_size=25&page=${pageParam}`;
		let response_json = await getData(apiURL, authTokens.access);
		return response_json;
	};

	const {
		isLoading: dataTypesLoading,
		isError: dataTypesIsError,
		isPending: dataTypesPending,
		data: dataTypes,
		error: dataTypeError,
	} = useQuery({
		queryKey: ["dataTypes"],
		queryFn: getDataTypesFunc,
		refetchOnWindowFocus: false,
	});

	const {
		data: deploymentData,
		error,
		fetchNextPage,
		hasNextPage,
		isFetching,
		isFetchingNextPage,
		status,
	} = useInfiniteQuery({
		queryKey: ["deployments"],
		queryFn: getDeploymentDataFunc,
		initialPageParam: 1,
		getNextPageParam: (lastPage, pages) => lastPage.next,
		refetchOnWindowFocus: false,
		enabled: !dataTypesPending,
	});

	useEffect(() => {
		if (hasNextPage && !isFetchingNextPage) {
			fetchNextPage();
		}
	}, [hasNextPage, isFetchingNextPage, fetchNextPage]);

	let sortedDeploymentData = [];

	const setBounds = useCallback(() => {
		if (!map) return;
		if (!sortedDeploymentData || sortedDeploymentData.length === 0) return;
		let allLat = [];
		let allLng = [];
		map.eachLayer(function (layer) {
			if (layer._latlng !== undefined) {
				allLat.push(layer._latlng.lat);
				allLng.push(layer._latlng.lng);
			}
		});
		try {
			map.fitBounds([
				[Math.min(...allLat) - 0.1, Math.min(...allLng) - 0.1],
				[Math.max(...allLat) + 0.1, Math.max(...allLng) + 0.1],
			]);
		} catch {}
	}, [map, sortedDeploymentData]);

	useEffect(() => {
		setBounds();
	}, [setBounds, hasNextPage]);

	if (!dataTypesLoading && dataTypes) {
		sortedDeploymentData = dataTypes.reduce((acc, dataType) => {
			acc[dataType.name] = [];
			return acc;
		}, {});

		if (deploymentData && deploymentData.pages !== undefined) {
			deploymentData.pages.forEach((group) => {
				if (group.results !== undefined) {
					group.results.forEach((deployment) => {
						sortedDeploymentData[deployment.device_type].push(deployment);
					});
				}
			});
		}
	}

	return status === "pending" ? (
		<Loading />
	) : status === "error" ? (
		<p>Error: {error.message}</p>
	) : (
		<>
			<MapContainer
				center={[0, 0]}
				zoom={3}
				scrollWheelZoom={true}
				style={{ height: "75vh", width: "100%" }}
				whenReady={(e) => setMap(e.target)}
			>
				<TileLayer
					attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
					url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
				/>

				<LayersControl position="topright">
					{Object.keys(sortedDeploymentData).map((key, i) => {
						let value = sortedDeploymentData[key];
						if (value.length === 0) {
							return null;
						}
						return (
							<LayersControl.Overlay
								name={key}
								checked
								key={i}
							>
								<FeatureGroup key={key}>
									{value.map((deployment) => {
										return DeploymentMarker(deployment);
									})}
								</FeatureGroup>
							</LayersControl.Overlay>
						);
					})}
				</LayersControl>

				<div className="leaflet-bottom leaflet-left">
					<div className="leaflet-control">
						{isFetching || hasNextPage ? (
							<Loading />
						) : (
							<ResetLocation
								handleChangeLatLong={(e) => {
									setBounds();
								}}
							/>
						)}
					</div>
				</div>
				<UserLocationMarker />
			</MapContainer>
		</>
	);
};
