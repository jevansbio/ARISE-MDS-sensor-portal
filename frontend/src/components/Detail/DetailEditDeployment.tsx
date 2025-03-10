import React, { useEffect, useState } from "react";
import DetailEditForm from "./DetailEditForm.tsx";
import JSONInput from "../JSONInput.tsx";
import FormMap from "../FormMap.tsx";
import FormDateTZSelect from "../FormDateTZSelect.tsx";
import FormSelectAPI from "../FormSelectAPI.tsx";
import UserSelector from "../UserSelector.tsx";
import PermissionEditor from "../PermissionEditor.tsx";

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

const DetailEditDeployment = ({
	selectedData,
	onSubmit,
	onCancel,
	setErrorDict,
	setWasValidated,
	onReset = () => {},
	errorDict = {},
	wasValidated = false,
}: Props) => {
	// deployment

	console.log("DATA IN DEPLOYMENT DETAIL EDIT");
	console.log(selectedData);

	const [deploymentID, setDeploymentID] = useState(
		selectedData ? selectedData["deployment_ID"] : ""
	);
	console.log(deploymentID);
	const [device_type_ID, setDevice_type_ID] = useState(
		selectedData ? selectedData["device_type_ID"] : null
	);
	const [device_n, setDevice_n] = useState(
		selectedData ? selectedData["device_n"] : 1
	);

	const [project_ID, setProject_ID] = useState(
		selectedData ? selectedData["project_ID"] : []
	);

	const [site_ID, setSite_ID] = useState(
		selectedData ? selectedData["site_ID"] : null
	);

	const [device_ID, setDevice_ID] = useState(
		selectedData ? selectedData["device_ID"] : null
	);

	const [deployment_start, setDeployment_start] = useState(
		selectedData ? selectedData["deployment_start"] : new Date().toJSON()
	);

	const [deployment_end, setDeployment_end] = useState(
		selectedData ? selectedData["deployment_end"] : null
	);

	const [latitude, setLatitude] = useState(
		selectedData ? selectedData["latitude"] : null
	);
	const [longitude, setLongitude] = useState(
		selectedData ? selectedData["longitude"] : null
	);

	const [extraInfo, setExtraInfo] = useState(
		selectedData ? selectedData["extra_data"] : {}
	);

	const setLatLong = function (latlong) {
		if (latlong) {
			setLatitude(Number(String(latlong.lat).substring(0, 7)));
			setLongitude(Number(String(latlong.lng).substring(0, 7)));
		} else {
			setLatitude(null);
			setLongitude(null);
		}
	};

	const resetDetailData = function () {
		onReset();
		//Deployment only
		setDeploymentID("");
		setDevice_type_ID(null);
		setDevice_n(null);
		setProject_ID([]);
		setSite_ID(null);
		setDevice_ID(null);
		setDeployment_start(new Date().toJSON());
		setDeployment_end(null);
		setLatLong(null);
		setExtraInfo({});
	};

	useEffect(() => {
		setDeploymentID(selectedData ? selectedData["deployment_ID"] : "");
		setDevice_type_ID(selectedData ? selectedData["device_type_ID"] : null);
		setDevice_n(selectedData ? selectedData["device_n"] : 1);
		setProject_ID(selectedData ? selectedData["project_ID"] : []);
		setSite_ID(selectedData ? selectedData["site_ID"] : null);
		setDevice_ID(selectedData ? selectedData["device_ID"] : null);
		setDeployment_start(
			selectedData ? selectedData["deployment_start"] : new Date().toJSON()
		);
		setDeployment_end(selectedData ? selectedData["deployment_end"] : null);
		setLatLong({
			lat: selectedData ? selectedData["latitude"] : null,
			lng: selectedData ? selectedData["longitude"] : null,
		});
		setExtraInfo(selectedData ? selectedData["extra_data"] : {});
	}, [selectedData]);

	// useEffect(() => {
	// 	handleFormChange();
	// }, [
	// 	device_type_ID,
	// 	project_ID,
	// 	site_ID,
	// 	device_ID,
	// 	deployment_start,
	// 	deployment_end,
	// 	latitude,
	// 	longitude,
	// 	extraInfo,
	// 	handleFormChange,
	// ]);

	return (
		<DetailEditForm
			objectType="deployment"
			setErrorDict={setErrorDict}
			wasValidated={wasValidated}
			setWasValidated={setWasValidated}
			selectedData={selectedData}
			onSubmit={onSubmit}
			onCancel={onCancel}
			onReset={resetDetailData}
			JSONFields={["project_ID", "extra_data"]}
		>
			<>
				{/* here starts the deployment fields */}
				<div className="row px-1 py-1 mb-3 border rounded">
					<div className="col-md-4">
						<label htmlFor="post-deployment_ID">Deployment ID</label>
						<input
							name="deployment_ID"
							className={`form-control ${
								wasValidated
									? errorDict["deployment_ID"]
										? "is-invalid"
										: "is-valid"
									: ""
							}`}
							id="post-deployment_ID"
							value={deploymentID}
							onChange={(e) => {
								setDeploymentID(e.target.value);
							}}
							required
						/>

						<div className="form-text">
							Identifier for this deployment.
							<div className="invalid-feedback">
								{errorDict["deployment_ID"]}
							</div>
						</div>
					</div>
					<div className="col-md-4">
						<label htmlFor="post-device_type_ID">Device type</label>
						<FormSelectAPI
							id="post-device_type_ID"
							name="device_type_ID"
							label="Device type"
							choices={[]}
							value={device_type_ID}
							apiURL="datatype/"
							valueKey="id"
							labelKey="name"
							handleChange={setDevice_type_ID}
							isClearable={false}
							valid={errorDict["device_type_ID"] === ""}
						/>
						<input
							hidden
							name="device_type_ID"
							value={device_type_ID ? device_type_ID : ""}
							required
						></input>

						<div className="form-text">
							Device type of your deployment
							<div className="invalid-feedback">
								{errorDict["device_type_ID"]}
							</div>
						</div>
					</div>
					<div className="col-md-auto">
						<label htmlFor="post-device_n">Device number</label>
						<input
							name="device_n"
							className={`form-control ${
								wasValidated
									? errorDict["device_n"]
										? "is-invalid"
										: "is-valid"
									: ""
							}`}
							id="post-device_n"
							value={device_n}
							type="number"
							onChange={setDevice_n}
							min={1}
							max={100}
							required
						/>
						<div className="form-text">
							Deployment ID number
							<div className="invalid-feedback">{errorDict["device_n"]}</div>
						</div>
					</div>
				</div>
				<div className="row py-1 px-1 mb-3 border rounded">
					<div className="col-md-4">
						<label htmlFor="post-device_ID">Device being deployed</label>
						<FormSelectAPI
							id="post-device_ID"
							name="device_ID"
							label="Device"
							choices={[]}
							value={device_ID}
							apiURL={device_type_ID ? `device/?type=${device_type_ID}` : ""}
							valueKey="id"
							labelKey="device_ID"
							creatable={false}
							isClearable={true}
							handleChange={setDevice_ID}
							valid={errorDict["device_ID"] === ""}
						/>
						<input
							hidden
							name="device_ID"
							value={device_ID ? device_ID : ""}
							required
						></input>
						<div className="form-text">
							Deployment device.
							<div className="invalid-feedback">{errorDict["device_ID"]}</div>
						</div>
					</div>
					<div className="col-md-4">
						<label htmlFor="post-project_ID">Project</label>
						<FormSelectAPI
							id="post-project_ID"
							name="project_ID"
							label="Projects"
							choices={[]}
							value={project_ID}
							apiURL="project/"
							valueKey="id"
							labelKey="project_ID"
							multiple={true}
							handleChange={setProject_ID}
							valid={errorDict["project_ID"] === ""}
						/>
						<input
							hidden
							name="project_ID"
							value={project_ID ? JSON.stringify(project_ID) : ""}
						></input>
						<div className="form-text">
							Projects to associate with deployment.
							<div className="invalid-feedback">{errorDict["project_ID"]}</div>
						</div>
					</div>
					<div className="col-md-4">
						<label htmlFor="post-site_ID">Site</label>
						<FormSelectAPI
							id="post-site_ID"
							name="site_ID"
							label="Site"
							choices={[]}
							value={site_ID}
							apiURL="site/"
							valueKey="id"
							labelKey="name"
							creatable={true}
							handleChange={setSite_ID}
							valid={errorDict["site_ID"] === ""}
						/>
						<input
							hidden
							name="site_ID"
							value={site_ID ? site_ID : ""}
							required
						></input>
						<div className="form-text">
							Deployment site. New sites can be added.
							<div className="invalid-feedback">{errorDict["site_ID"]}</div>
						</div>
					</div>
				</div>
				<div className="row py-1 px-3 mb-3 border rounded">
					<div className="col-md-6 ps-md-0 pe-md-1">
						<label htmlFor="post-deployment_start">Deployment start</label>
						<FormDateTZSelect
							id="post-deployment_start"
							name="deployment_start"
							label="Deployment started"
							text="Date and time deployment starts."
							defaultvalue={deployment_start}
							handleChange={setDeployment_start}
							required={true}
							valid={
								errorDict["deployment_start"] === "" &&
								errorDict["deployment_start_TZ"] === "" &&
								errorDict["deployment_start_dt"] === ""
							}
							validated={wasValidated}
						/>
						<div className="form-text">
							Deployment start date time.
							<div className="invalid-feedback">
								{`${errorDict["deployment_start"]} ${errorDict["deployment_start_TZ"]} ${errorDict["deployment_start_dt"]}`}
							</div>
						</div>
					</div>
					<div className="col-md-6 ps-md-1 pe-md-0">
						<label htmlFor="post-deployment_end">Deployment end</label>
						<FormDateTZSelect
							id="post-deployment_end"
							name="deployment_end"
							label="Deployment ended"
							text="Date and time deployment ends."
							defaultvalue={deployment_end}
							handleChange={setDeployment_end}
							valid={
								errorDict["deployment_end"] === "" &&
								errorDict["deployment_end_TZ"] === "" &&
								errorDict["deployment_end_dt"] === ""
							}
							validated={wasValidated}
						/>
						<div className="form-text">
							Deployment end date time. Can be left blank.
							<div className="invalid-feedback">{`${errorDict["deployment_end"]} ${errorDict["deployment_end_TZ"]} ${errorDict["deployment_end_dt"]}`}</div>
						</div>
					</div>
				</div>
				<div className="row py-1 mb-3 border rounded">
					<label htmlFor="post-latitude">Location</label>
					<div className="col-6">
						<input
							name="latitude"
							id="post-latitude"
							type="number"
							className={`form-control ${
								wasValidated
									? errorDict["latitude"]
										? "is-invalid"
										: "is-valid"
									: ""
							}`}
							value={latitude}
							onChange={(e) => {
								setLatLong({
									lat: e.target.value,
									lng: longitude,
								});
							}}
						/>
						<div className="form-text mb-1">
							Latitude.
							<div className="invalid-feedback">{errorDict["latitude"]}</div>
						</div>
					</div>
					<div className="col-6">
						<input
							name="longitude"
							id="post-longitude"
							type="number"
							className={`form-control ${
								wasValidated
									? errorDict["longitude"]
										? "is-invalid"
										: "is-valid"
									: ""
							}`}
							value={longitude}
							onChange={(e) => {
								setLatLong({
									lat: latitude,
									lng: e.target.value,
								});
							}}
						/>
						<div className="form-text mb-1">
							Longitude.
							<div className="invalid-feedback">{errorDict["longitude"]}</div>
						</div>
					</div>

					<FormMap
						latitude={latitude}
						longitude={longitude}
						handleChangeLatLong={setLatLong}
					/>
				</div>
				<div className="row py-1 mb-3 border rounded">
					<label htmlFor="post-extra_data">Extra fields</label>
					<JSONInput
						id="post-extra_data"
						name="extra_data"
						value={extraInfo}
						onJSONchange={setExtraInfo}
						wasValidated={wasValidated}
						errorDict={errorDict["extra_data"] ? errorDict["extra_data"] : {}}
					/>
				</div>

				{/* here ends the deployment fields */}
			</>
		</DetailEditForm>
	);
};

export default DetailEditDeployment;
