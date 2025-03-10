import React, { useEffect } from "react";
import { Marker, useMap, useMapEvent } from "react-leaflet";
import { Icon, LeafletMouseEvent, LatLngExpression } from "leaflet";

interface Props {
	readOnly?: boolean;
	formLatLong: { lat: number | null; lng: number | null } | null;
	handleChangeLatLong: (latlng: LeafletMouseEvent["latlng"]) => void;
}

const FormMapMarker = ({
	readOnly = false,
	formLatLong = null,
	handleChangeLatLong = () => {},
}: Props) => {
	const defaultIcon = new Icon({
		iconUrl:
			"https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
		iconSize: [25, 41],
		iconAnchor: [12, 41],
		popupAnchor: [1, -34],
		shadowSize: [41, 41],
	});

	//const [mapLocation, setMapLocation] = useState(
	//	formLatLong ? formLatLong : null
	//);
	let mapLocation = formLatLong ? formLatLong : null;

	const map = useMap();

	useEffect(() => {
		if (mapLocation !== null) {
			map.setView(mapLocation as LatLngExpression);
		}
	}, [map, mapLocation]);

	const mapLocate = useMapEvent("locationfound", (e) => {
		if (mapLocation == null) {
			mapLocation = e.latlng;
			handleChangeLatLong(e.latlng);
			map.setView(e.latlng);
		}
	});

	const mapClick = useMapEvent("click", (e) => {
		if (!readOnly) {
			map.setView(e.latlng, map.getZoom());
			handleChangeLatLong(e.latlng);
			mapLocation = e.latlng;
		}
	});

	console.log(formLatLong ? true : false);
	console.log(formLatLong);
	console.log(mapLocation);

	return mapLocation === null ? null : (
		<Marker
			position={mapLocation as LatLngExpression}
			icon={defaultIcon}
			interactive={false}
		></Marker>
	);
};

export default FormMapMarker;
