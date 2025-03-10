import React from "react";
import { dtFormat } from "../../utils/timezoneFunctions";
import { capitalizeFirstLetter } from "../../utils/generalFunctions";

interface Props {
	selectedData: object | null;
	displayKeys?: string[];
	timeKeys?: string[];
	jsonKeys?: string[];
}

const DetailDisplayTable = ({
	selectedData,
	displayKeys = [],
	timeKeys = [],
	jsonKeys = ["extra_data"],
}: Props) => {
	const convertDates = function (key, value) {
		if (timeKeys.includes(key)) {
			let currentTime = value;

			console.log(currentTime);
			let dateTime = new Date(currentTime);
			console.log(dateTime);
			return dtFormat.format(dateTime);
		} else {
			return value;
		}
	};

	const tableRow = function (key, value) {
		if (!displayKeys.includes(key) || value === null) {
			return null;
		}

		value = convertDates(key, value);

		let value_result;

		if (jsonKeys.includes(key)) {
			value_result = (
				<td className="extra-info-table p-0 border">
					<table className="table table-sm mb-0 align-middle text-center">
						<tbody>
							{Object.keys(value).map((e_iKey, i) => {
								return (
									<tr key={`${key}_${e_iKey}`}>
										<th scope="row">
											{capitalizeFirstLetter(e_iKey.replace(/_/g, " "))}
										</th>
										<td>{String(value[e_iKey])}</td>
									</tr>
								);
							})}
						</tbody>
					</table>
				</td>
			);
		} else {
			value_result = <td>{value === null ? value : String(value)}</td>;
		}

		return (
			<tr key={key}>
				<th scope="row">{capitalizeFirstLetter(key.replace(/_/g, " "))}</th>
				{value_result}
			</tr>
		);
	};

	return selectedData ? (
		<table className="table detail-table">
			<tbody>
				{displayKeys.map((key, i) => {
					return tableRow(key, selectedData[key]);
				})}
			</tbody>
		</table>
	) : null;
};

export default DetailDisplayTable;
