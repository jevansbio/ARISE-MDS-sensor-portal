import { useRef, useEffect } from "react";
import { useMap } from "react-leaflet";
import { DomEvent } from "leaflet";

interface Props {
	handleChangeLatLong: () => void;
}

const ResetLocation = ({ handleChangeLatLong = () => {} }: Props) => {
	const ref = useRef(null);

	useEffect(() => {
		if (ref.current) {
			DomEvent.disableClickPropagation(ref.current);
		}
	});

	const map = useMap();

	const resetLocation = function(e: any) {
		map.locate();
		handleChangeLatLong();
	};

	return (
		<button
			type="button"
			ref={ref}
			onClick={resetLocation}
			className="btn reset-location-button btn-danger btn-lg"
		>
			Reset location
		</button>
	);
};

export default ResetLocation;
