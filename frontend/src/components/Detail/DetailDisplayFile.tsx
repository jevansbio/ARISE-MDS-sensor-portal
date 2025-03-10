import React from "react";
import { Link } from "react-router-dom";

interface Props {
	fileName: string;
	fileURL: string;
	fileFormat: string;
}

const DetailDisplayFile = ({ fileName, fileURL, fileFormat }: Props) => {
	const isImage = [".jpg", ".jpeg", ".png"].includes(fileFormat.toLowerCase());

	return (
		<div>
			<a
				href={fileURL}
				target="_blank'"
			>
				{isImage ? (
					<img
						src={fileURL}
						alt={fileName}
						style={{
							"object-fit": "contain",
							width: "100%",
							"max-height": "40rem",
						}}
					/>
				) : (
					"Download File"
				)}
			</a>
		</div>
	);
};

export default DetailDisplayFile;
