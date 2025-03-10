import React, { useContext, useState } from "react";
import { postData } from "../../utils/FetchFunctions.js";
import { useMutation } from "@tanstack/react-query";
import AuthContext from "../../context/AuthContext.jsx";

interface Props {
	id: number;
	favourite: boolean;
}

const FavouriteButton = ({ id, favourite }: Props) => {
	const { authTokens } = useContext(AuthContext);
	const [isFavourite, setIsFavourite] = useState(favourite);

	const newPOST = async function (x: { apiURL: string; newData: object }) {
		let response_json = await postData(x.apiURL, authTokens.access, x.newData);
		return response_json;
	};

	const doPost = useMutation({
		mutationFn: (inputValue: { apiURL: string; newData: object }) =>
			newPOST(inputValue),
	});

	const onClickFunction = async function (e) {
		let response = await doPost.mutateAsync({
			apiURL: `datafile/${id}/favourite_file/`,
			newData: {},
		});
		if (response.ok) {
			if (isFavourite) {
				setIsFavourite(false);
			} else {
				setIsFavourite(true);
			}
		}
	};

	return (
		<button
			className={`btn w-100 mt-1 ${
				isFavourite ? "btn-secondary" : "btn-outline-secondary"
			}`}
			onClick={onClickFunction}
		>
			{isFavourite ? "Unfavourite file" : "Favourite file"}
		</button>
	);
};

export default FavouriteButton;
