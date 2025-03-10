import React from "react";
import "../../styles/gallerytile.css";

interface Props {
	cardTitle: string;
	cardText?: string;
	cardImageURL?: string;
	index: number;
	extraClasses: string;
	onClick?: (int) => void;
}

const GalleryTile = ({
	cardTitle = "",
	cardText = "",
	cardImageURL = "",
	index = 0,
	extraClasses = "",
	onClick = (int) => {},
}: Props) => {
	const getImage = function () {
		console.log(cardImageURL);
		if (cardImageURL !== null && cardImageURL !== "") {
			return (
				<img
					className="card-img-top"
					src={cardImageURL}
					alt=""
					loading="lazy"
					style={{ maxHeight: "160px" }}
				/>
			);
		} else {
			return (
				<svg
					className="bd-placeholder-img card-img-top"
					width="100%"
					height="160px"
					xmlns="http://www.w3.org/2000/svg"
					role="img"
					preserveAspectRatio="xMidYMid slice"
					focusable="false"
					style={{ maxHeight: "160px" }}
				>
					<title>Placeholder</title>
					<rect
						width="100%"
						height="100%"
						fill="white"
					></rect>
				</svg>
			);
		}
	};

	const handleOnClick = function (e) {
		console.log(index);
		onClick(index);
	};

	return (
		<div
			className={"card h-100 p-2 " + extraClasses}
			id={`card_${index}`}
			onClick={handleOnClick}
		>
			{getImage()}
			<div className="card-body">
				<h6
					className="card-title"
					style={{ fontSize: "0.75rem" }}
				>
					{cardTitle}
				</h6>
				<p className="card-text">
					{cardText}
					<small className="text-muted"></small>
				</p>
			</div>
		</div>
	);
};

export default GalleryTile;
