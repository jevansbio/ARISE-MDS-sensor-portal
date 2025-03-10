import React from "react";
import GalleryTile from "./GalleryTile.tsx";
import { useOutletContext } from "react-router-dom";

interface Props {
	objectType: string;
	data: [];
	onTileClick: (index) => void;
}

const GalleryDisplay = ({
	objectType,
	data = [],
	onTileClick = () => {},
}: Props) => {
	const { nameKey } = useOutletContext();
	let thumbKey = "";
	let textKey = "";
	if (objectType === "deployment") {
		thumbKey = "thumb_url";
		textKey = "site";
	} else if (objectType === "datafile") {
		thumbKey = "thumb_url";
		textKey = "recording_dt";
	} else if (objectType === "device") {
		textKey = "type";
	}

	return (
		<div
			id="gallery-rows"
			className="row row-cols-1 row-cols-lg-5 justify-content-start g-2 p-2"
		>
			{data.map((x, index) => {
				let imageURL = x[thumbKey];
				let extraClasses = "";
				if (objectType !== "datafile") {
					x["is_active"]
						? (extraClasses = "")
						: (extraClasses = "text-white bg-secondary");
				}
				return (
					<div className="col">
						<GalleryTile
							cardTitle={x[nameKey]}
							cardText={x[textKey]}
							cardImageURL={imageURL}
							index={index}
							key={`tile_${index}`}
							extraClasses={extraClasses}
							onClick={onTileClick}
						/>
					</div>
				);
			})}
		</div>
	);
};

export default GalleryDisplay;
