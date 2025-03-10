import React from "react";
import { Link, useOutletContext } from "react-router-dom";

interface Props {
	selectedData: object;
	objectType: number;
}

const DetailDisplayParents = ({ selectedData, objectType }: Props) => {
	const { validParents } = useOutletContext() as object;

	const getButtons = function () {
		return validParents.map((validParent) => {
			console.log(validParent);
			console.log(selectedData);
			let currentName = selectedData[validParent];
			let current_IDs = selectedData[validParent + "_ID"];
			if (Array.isArray(current_IDs)) {
				return (
					<div className="dropdown p-2 flex-fill">
						<button
							className="btn btn-primary w-100 dropdown-toggle"
							id="dropdownMenuButton1"
							data-bs-toggle="dropdown"
						>
							Go to {validParent}
						</button>
						<ul className="dropdown-menu w-100">
							{current_IDs.map((current_ID, i) => {
								currentName = selectedData[validParent][i];
								return (
									<li>
										<Link
											to={`/${validParent}s/${current_ID}`}
											className="dropdown-item "
										>
											Go to {validParent} {currentName}
										</Link>
									</li>
								);
							})}
						</ul>
					</div>
				);
			} else {
				return (
					<Link
						to={`/${validParent}s/${current_IDs}`}
						key={validParent}
						className="p-2 flex-fill"
					>
						<button className="btn btn-primary w-100">
							Go to {validParent} {currentName}
						</button>
					</Link>
				);
			}
		});
	};

	return <div className="d-flex justify-content-evenly">{getButtons()}</div>;
};

export default DetailDisplayParents;
