import React, { useState } from "react";
import DetailEditForm from "./DetailEditForm.tsx";

interface Props {
	selectedData?: object | null;
	onSubmit?: (e: Event, addNew: boolean, response: object) => void;
	onCancel?: (e: any) => void;
	setErrorDict: (newVal: object) => void;
	setWasValidated: (newVal: boolean) => void;
	onReset: () => void;
	errorDict: object;
	wasValidated: boolean;
}

const DetailEditProject = ({
	selectedData,
	onSubmit,
	onCancel,
	setErrorDict,
	setWasValidated,
	onReset = () => {},
	errorDict = {},
	wasValidated = false,
}: Props) => {
	const [projectID, setProjectID] = useState(
		selectedData ? selectedData["project_ID"] : null
	);
	const [projectName, setProjectName] = useState(
		selectedData ? selectedData["name"] : null
	);

	const resetDetailData = function () {
		onReset();
		setProjectName("");
		setProjectID("");
	};

	return (
		<DetailEditForm
			objectType="project"
			setErrorDict={setErrorDict}
			wasValidated={wasValidated}
			setWasValidated={setWasValidated}
			selectedData={selectedData}
			onSubmit={onSubmit}
			onCancel={onCancel}
			onReset={resetDetailData}
		>
			<>
				<div className="row px-1 py-1 mb-3 border rounded">
					<div className="col-md-4">
						<label htmlFor="post-project_ID">Project ID</label>
						<input
							name="project_ID"
							className={`form-control ${
								wasValidated
									? errorDict["project_ID"]
										? "is-invalid"
										: "is-valid"
									: ""
							}`}
							id="post-project_ID"
							value={projectID}
							onChange={(e) => {
								setProjectID(e.target.value);
							}}
							required
						/>

						<div className="form-text">
							Short identifier for this project.
							<div className="invalid-feedback">{errorDict["project_ID"]}</div>
						</div>
					</div>
					<div className="col-md-4">
						<label htmlFor="post-name">Oroject name</label>
						<input
							name="name"
							className={`form-control ${
								wasValidated
									? errorDict["name"]
										? "is-invalid"
										: "is-valid"
									: ""
							}`}
							id="post-name"
							value={projectName}
							onChange={(e) => {
								setProjectName(e.target.value);
							}}
							required
						/>

						<div className="form-text">
							Full name for project.
							<div className="invalid-feedback">{errorDict["name"]}</div>
						</div>
					</div>
				</div>
			</>
		</DetailEditForm>
	);
};
export default DetailEditProject;
