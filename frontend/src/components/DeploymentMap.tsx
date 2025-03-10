import React, { useCallback, useEffect, useRef, useState } from "react";
import {
	FeatureGroup,
	LayerGroup,
	MapContainer,
	Popup,
	TileLayer,
	Marker,
} from "react-leaflet";
import UserLocationMarker from "./MapUserLocationMarker.tsx";
import ResetLocation from "./MapControlResetLocation.tsx";

import { Icon } from "leaflet";
import { Marker as CompMarker } from "@adamscybot/react-leaflet-component-marker";
import "../BeautifyMarker/leaflet-beautify-marker-icon.css";
import { IconPickerItem } from "react-icons-picker";

import logo from "../snyper4g.png";

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
					<IconPickerItem
						value={symbol}
						size={symbolSize}
						color={textColor}
					/>

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

	const featureGroupRef = useRef();
	const [map, setMap] = useState(null);

	const setBounds = useCallback(() => {
		if (!map) return;
		console.log(map);
		let newBounds = featureGroupRef.current.getBounds();
		map.fitBounds(newBounds);
	}, [map]);

	useEffect(() => {
		setBounds();
	}, [map, setBounds]);

	return (
		<div>
			<MapContainer
				center={[0, 0]}
				zoom={1}
				scrollWheelZoom={true}
				style={{ height: "75vh", width: "100%" }}
				whenReady={(e) => setMap(e.target)}
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
											borderColor="blue"
											textColor="blue"
										/>
									}
								>
									<Popup>{deploymentData.deployment_device_ID}</Popup>
								</CompMarker>
							</>
						);
					})}
				</FeatureGroup>
				<UserLocationMarker />
				<ResetLocation
					handleChangeLatLong={(e) => {
						setBounds();
					}}
				/>
			</MapContainer>
		</div>
	);
};

export default DeploymentMap;
