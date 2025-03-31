import { useCallback, useEffect, useRef, useState } from "react";
import {
	FeatureGroup,
	MapContainer,
	Popup,
	TileLayer,
} from "react-leaflet";
import { Map as LeafletMap, FeatureGroup as LeafletFeatureGroup} from "leaflet";
import { Icon } from "leaflet";
import "../../../misc/BeautifyMarker/leaflet-beautify-marker-icon.css";
import { Marker as CompMarker } from "@adamscybot/react-leaflet-component-marker";

//import logo from "../snyper4g.png";
import UserLocationMarker from "../MapUserLocationMarker";
import ResetLocation from "../MapControlResetLocation";
import { Link } from "@tanstack/react-router";

interface Props {
	//should be changed from any
	deployments: [{ latitude: any; longitude: any; deployment_device_ID: any, extra_data: any }];
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

const DeploymentIcon = ({
	borderColor = "#1EB300",
	borderStyle = "solid",
	backgroundColor = "white",
	textColor = "#000",
	borderWidth = 2,
	iconSize = [28, 28],
	symbolSize = 16,
	symbol = "FaCamera",
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
					{/* <img
						style={{ height: "100%", objectFit: "cover" }}
						src={logo}
						alt="Logo"
					/> */}
				</div>
			</div>
		</div>
	);
};

const DeploymentMap = ({ deployments }: Props) => {
	const defaultIcon = new Icon({
		iconUrl:
			"https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
		iconSize: [25, 41],
		iconAnchor: [12, 41],
		popupAnchor: [1, -34],
		shadowSize: [41, 41],
	});

	const featureGroupRef = useRef<LeafletFeatureGroup | null>(null);
  	const [map, setMap] = useState<LeafletMap | null>(null);
	const mapRef = useRef<LeafletMap | null>(null);

	const setBounds = useCallback(() => {
		if (!map || !featureGroupRef.current) return;
		const newBounds = featureGroupRef.current.getBounds();
		map.fitBounds(newBounds);
	}, [map]);

	useEffect(() => {
		setBounds();
	}, [map, setBounds]);

	console.log(deployments.map((deploymentData) => deploymentData.extra_data.device_config.device_ID));

	return (
		<div>
			<MapContainer
				ref={mapRef}
				center={[0, 0]}
				zoom={1}
				scrollWheelZoom={true}
				style={{ height: "75vh", width: "100%" }}
				whenReady={() => {
					if (mapRef.current) {
					setMap(mapRef.current);
					}
				}}
			>

				<TileLayer
					attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
					url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
				/>
				<FeatureGroup ref={featureGroupRef}>
					{deployments.map((deploymentData) => {
						let latLng = {
							lat: deploymentData.latitude,
							lng: deploymentData.longitude,
						};
						return (
							<>
								<CompMarker
									position={latLng}
									icon={
										<DeploymentIcon
											borderColor="red"
											textColor="red"
										/>
									}
								>
									<Popup>
									<Link
										to="/devices/$deviceId"
										params={{ deviceId: deploymentData.extra_data.device_config.device_ID }}
										className="text-blue-500 hover:underline"
									>
										View Device: {deploymentData.extra_data.device_config.device_ID}
									</Link>
									</Popup>
								</CompMarker>
							</>
						);
					})}
				</FeatureGroup>
				<UserLocationMarker />
				<ResetLocation
					handleChangeLatLong={() => {
						setBounds();
					}}
				/>
			</MapContainer>
		</div>
	);
};

export default DeploymentMap;
