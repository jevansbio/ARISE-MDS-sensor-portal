import React from "react";

interface Props {
	tableID: string;
	userData?: [];
	button?: boolean;
	buttonOnClick?: (number) => void;
	buttonClass?: string;
	buttonText?: string;
}

const UserTable = ({
	tableID = "",
	userData = [],
	button = false,
	buttonOnClick = (number) => {},
	buttonClass = "",
	buttonText = "",
}: Props) => {
	const hideKeys = ["id"];

	console.log(userData);

	const tableRow = (currentData, index) => {
		return (
			<tr key={index}>
				{Object.keys(currentData).map((key, i) => {
					if (hideKeys.includes(key)) {
						return null;
					}
					return <td key={`${index}_${key}`}>{currentData[key]}</td>;
				})}
				<td>
					{button ? (
						<button
							className={buttonClass}
							onClick={(e) => {
								e.preventDefault();
								buttonOnClick(currentData["id"]);
							}}
						>
							{buttonText}
						</button>
					) : null}
				</td>
			</tr>
		);
	};

	const tableHead = (currentData) => {
		console.log(currentData);
		return (
			<tr key={0}>
				{Object.keys(currentData).map((key, i) => {
					if (hideKeys.includes(key)) {
						return null;
					}
					return (
						<th
							key={`0_${key}`}
							id={`0_${key}`}
						>
							{key.replace("_", " ")}
						</th>
					);
				})}
				<th></th>
			</tr>
		);
	};

	if (userData.length === 0) {
		return;
	}

	return (
		<table className="w-100 table">
			<thead>{tableHead(userData[0])}</thead>
			<tbody>
				{userData.map((currentData, i) => {
					return tableRow(currentData, i);
				})}
			</tbody>
		</table>
	);
};

export default UserTable;
