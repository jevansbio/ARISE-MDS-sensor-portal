import { useState, useEffect } from "react";
import { useMap, Circle } from "react-leaflet";
import { LatLng } from "leaflet";

const UserLocationMarker = () => {
	const [position, setPosition] = useState<LatLng>();
	const [radius, setRadius] = useState(0);

	const map = useMap();

	useEffect(() => {
		map.locate().on("locationfound", function (e) {
			console.log("location found");
			setPosition(e.latlng);
			setRadius(e.accuracy);
		});
	}, [map]);
	return position === undefined ? null : (
		<Circle
			center={position}
			radius={radius}
			//Known leaflet ts error, see https://github.com/PaulLeCam/react-leaflet/issues/1077
			interactive={false}
		/>
	);
};

export default UserLocationMarker;
