import React, { useState } from "react";
import DetailEditForm from "./DetailEditForm.tsx";
import JSONInput from "../JSONInput.tsx";
import FormSelectAPI from "../FormSelectAPI.tsx";

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

const DetailEditDevice = ({
	selectedData,
	onSubmit,
	onCancel,
	setErrorDict,
	setWasValidated,
	onReset = () => {},
	errorDict = {},
	wasValidated = false,
}: Props) => {
	const [typeID, setTypeID] = useState(
		selectedData ? selectedData["type_ID"] : null
	);
	const [deviceID, setDeviceID] = useState(
		selectedData ? selectedData["device_ID"] : null
	);
	const [deviceName, setDeviceName] = useState(
		selectedData ? selectedData["name"] : null
	);
	const [extraData, setExtraData] = useState(
		selectedData ? selectedData["extra_data"] : {}
	);

	const [autoUpdate, setAutoUpdate] = useState(
		selectedData ? selectedData["autoupdate"] : true
	);

	const [updateTime, setUpdateTime] = useState(
		selectedData ? selectedData["update_time"] : 48
	);

	const resetDetailData = function () {
		onReset();
		setDeviceID("");
		setDeviceName("");
		setTypeID(null);
		setExtraData({});
		setAutoUpdate(true);
		setUpdateTime(48);
	};

	console.log(selectedData);
	console.log(typeID);

	return (
		<DetailEditForm
			objectType="device"
			setErrorDict={setErrorDict}
			wasValidated={wasValidated}
			setWasValidated={setWasValidated}
			selectedData={selectedData}
			onSubmit={onSubmit}
			onCancel={onCancel}
			onReset={resetDetailData}
			JSONFields={["extra_data"]}
		>
			<>
				<div className="row px-1 py-1 mb-3 border rounded">
					<div className="col-md-4">
						<label htmlFor="post-device_ID">Device ID</label>
						<input
							name="device_ID"
							className={`form-control ${
								wasValidated
									? errorDict["device_ID"]
										? "is-invalid"
										: "is-valid"
									: ""
							}`}
							id="post-device_ID"
							value={deviceID}
							onChange={(e) => {
								setDeviceID(e.target.value);
							}}
							required
						/>

						<div className="form-text">
							Identifier for this device.
							<div className="invalid-feedback">{errorDict["device_ID"]}</div>
						</div>
					</div>
					<div className="col-md-4">
						<label htmlFor="post-name">Device name</label>
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
							value={deviceName}
							onChange={(e) => {
								setDeviceName(e.target.value);
							}}
							required
						/>

						<div className="form-text">
							Alternative name for device.
							<div className="invalid-feedback">{errorDict["name"]}</div>
						</div>
					</div>
				</div>
				<div className="row px-1 py-1 mb-3 border rounded">
					<div className="col-md-4">
						<label htmlFor="post-type_ID">Device type</label>
						<FormSelectAPI
							id="post-type_ID"
							name="type_ID"
							label="Device type"
							choices={[]}
							value={typeID}
							apiURL="datatype/"
							valueKey="id"
							labelKey="name"
							handleChange={setTypeID}
							isClearable={false}
							valid={errorDict["type_ID"] === ""}
						/>
						<input
							hidden
							id="hidden-post-type_ID"
							name="type_ID"
							value={typeID ? typeID : ""}
							required
						></input>

						<div className="form-text">
							Device type.
							<div className="invalid-feedback">{errorDict["type_ID"]}</div>
						</div>
					</div>
				</div>
				<div className="row px-1 py-1 mb-3 border rounded">
					<div className="col-md-4">
						<label htmlFor="post-autoupdate">Device auto updating</label>
						<div
							className={`form-check form-switch form-control  ${
								wasValidated
									? errorDict["autoupdate"]
										? "is-invalid"
										: "is-valid"
									: ""
							}`}
						>
							<label htmlFor="post-autoupdate">Auto update</label>
							<input
								name="autoupdate"
								className="form-check-input form-control"
								id="post-autoupdate"
								value={autoUpdate ? "true" : "false"}
								type="checkbox"
								onChange={(e) => {
									setAutoUpdate(e.target.checked);
								}}
							/>
						</div>
						<div className="form-text">
							Is device is expected to transmit files?
							<div className="invalid-feedback">{errorDict["autoupdate"]}</div>
						</div>
					</div>
					{autoUpdate ? (
						<div className="col-md-4">
							<label htmlFor="post-update_time">Update time</label>
							<input
								name="update_time"
								className={`form-control ${
									wasValidated
										? errorDict["update_time"]
											? "is-invalid"
											: "is-valid"
										: ""
								}`}
								id="post-update_time"
								value={updateTime}
								type="number"
								onChange={setUpdateTime}
								min={1}
							/>
							<div className="form-text">
								Expected update (hours)
								<div className="invalid-feedback">
									{errorDict["update_time"]}
								</div>
							</div>
						</div>
					) : null}
				</div>
				<div className="row px-1 py-1 mb-3 border rounded">
					<label htmlFor="post-extra_data">Extra fields</label>
					<JSONInput
						id="post-extra_data"
						name="extra_data"
						value={extraData}
						onJSONchange={setExtraData}
						wasValidated={wasValidated}
						errorDict={errorDict["extra_data"] ? errorDict["extra_data"] : {}}
					/>
				</div>
			</>
		</DetailEditForm>
	);
};

export default DetailEditDevice;
