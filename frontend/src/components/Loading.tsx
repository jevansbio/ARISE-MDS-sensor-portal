import React from "react";
import "../styles/loading.css";

interface Props {
	enabled?: boolean;
	showText?: boolean;
	large?: boolean;
}

const Loading = ({ enabled = true, showText = true, large = true }: Props) => {
	if (!enabled) {
		return null;
	}
	return (
		<div
			id="loading-div"
			className="text-center loading-div"
		>
			<div
				className={`spinner-border ${
					large ? "spinner-border-lg" : "spinner-border-sm"
				}`}
				role="status"
			></div>
			{showText ? <span className="spinner-text">Loading...</span> : null}
		</div>
	);
};

export default Loading;
