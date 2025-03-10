import { keepPreviousData, useQuery } from "@tanstack/react-query";
import React, { useContext, useState } from "react";
import { getData } from "../utils/FetchFunctions";
import UserTable from "./UserTable.tsx";
import AuthContext from "../context/AuthContext.jsx";
import Loading from "./Loading.tsx";

interface Props {
	chosenUsers: Number[];
	onPermissionChange: (newValue: number[]) => void;
}

const UserSelector = ({
	chosenUsers = [],
	onPermissionChange = (newValue: number[]) => {},
}: Props) => {
	const { authTokens } = useContext(AuthContext);

	const [searchString, setSearchString] = useState("");
	//get chosen user data

	console.log(chosenUsers);

	const {
		data: chosenData,
		isLoading: chosenDataLoading,
		isPending: chosenDataPending,
	} = useQuery({
		queryKey: ["chosenData", chosenUsers],
		queryFn: () =>
			getDataFunc(
				`user/?id__in=${chosenUsers.length ? chosenUsers : -1}&page_size=100`
			),
		placeholderData: keepPreviousData,
	});

	const {
		data: searchData,
		isLoading: searchDataLoading,
		isPending: searchDataPending,
	} = useQuery({
		queryKey: ["searchData_" + searchString + chosenUsers],
		queryFn: () =>
			getDataFunc(
				`user/?id__not_in=${
					chosenUsers.length ? chosenUsers : -1
				}&search=${searchString}&page_size=10`
			),
		enabled: searchString !== "",
		placeholderData: keepPreviousData,
	});

	const getDataFunc = async (apiURL) => {
		let response_json = await getData(apiURL, authTokens.access);
		return response_json;
	};

	const handleAddClick = (clickedUserID) => {
		let newChosenUsers = chosenUsers.concat(clickedUserID);
		console.log(newChosenUsers);
		onPermissionChange(newChosenUsers);
	};

	const handleRemoveClick = (clickedUserID) => {
		let newChosenUsers = chosenUsers.filter(
			(userID) => userID != clickedUserID
		);
		console.log("Remove", newChosenUsers);
		onPermissionChange(newChosenUsers);
	};

	return (
		<>
			{chosenDataLoading || chosenDataPending ? (
				<Loading />
			) : (
				<UserTable
					tableID="existing_users"
					userData={chosenData["results"]}
					buttonText="Remove"
					button={true}
					buttonClass="btn btn-danger"
					buttonOnClick={handleRemoveClick}
				/>
			)}
			Search users:{" "}
			<input
				value={searchString}
				onChange={(e) => {
					setSearchString(e.target.value);
				}}
			/>
			{searchString !== "" ? (
				searchDataLoading || searchDataPending ? (
					<Loading />
				) : (
					<UserTable
						tableID="search_users"
						userData={searchData["results"]}
						buttonText="Add"
						button={true}
						buttonClass="btn btn-primary"
						buttonOnClick={handleAddClick}
					/>
				)
			) : null}
		</>
	);
};

export default UserSelector;
