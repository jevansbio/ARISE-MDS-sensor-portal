import React, { ReactElement, useCallback } from "react";
import { Form } from "react-router-dom";
import { useState, useRef, useContext } from "react";
import { useMutation } from "@tanstack/react-query";
import AuthContext from "../../context/AuthContext.jsx";
import { patchData, postData } from "../../utils/FetchFunctions.js";
import toast from "react-hot-toast";
import PermissionEditor from "../PermissionEditor.tsx";

interface Props {
	children?: ReactElement;
	objectType: string;
	selectedData?: object | null;
	onSubmit?: (e: Event, addNew: boolean, response: object) => void;
	onCancel?: (e: any) => void;
	onReset?: () => void;
	setErrorDict: (newVal: object) => void;
	setWasValidated: (newVal: boolean) => void;
	wasValidated: boolean;
	JSONFields?: string[];
}

const DetailEditForm = ({
	children,
	objectType,
	selectedData = null,
	onSubmit = (e, addNew, response) => {},
	onCancel = () => {},
	onReset = () => {},
	setErrorDict = (newVal) => {},
	setWasValidated = (newVal) => {},
	wasValidated = false,
	JSONFields = [],
}: Props) => {
	const { authTokens } = useContext(AuthContext);

	const formRef = useRef<HTMLFormElement>(null);
	const [stopEdit, setStopEdit] = useState(false);

	const [managers_ID, setManagers_ID] = useState(
		selectedData ? selectedData["managers_ID"] : []
	);

	const [viewers_ID, setViewers_ID] = useState(
		selectedData ? selectedData["viewers_ID"] : []
	);

	const [annotators_ID, setAnnotators_ID] = useState(
		selectedData ? selectedData["annotators_ID"] : []
	);

	console.log(!selectedData);

	if (
		!selectedData ||
		Object.keys(selectedData as object).includes("managers_ID")
	) {
		JSONFields = JSONFields.concat([
			"managers_ID",
			"viewers_ID",
			"annotators_ID",
		]);
	}

	const doValidation = useCallback(
		function (responseData = null) {
			console.log("VALIDATE");
			let form = formRef.current;
			if (form === null) {
				return;
			}

			let newErrorDict = {};
			let valid = true;
			for (const input of form.getElementsByTagName("input")) {
				if (!responseData) {
					newErrorDict[input.name] = input.validationMessage;
				} else {
					let responseError = responseData[input.name];
					if (responseError) {
						newErrorDict[input.name] = responseData[input.name];
					} else {
						newErrorDict[input.name] = "";
					}
				}
				if (newErrorDict[input.name] !== "") {
					valid = false;
				}
			}

			setErrorDict(newErrorDict);
			console.log(newErrorDict);
			return valid;
		},
		[setErrorDict]
	);

	const handleFormChange = useCallback(
		function () {
			console.log("Form change " + wasValidated);
			if (wasValidated) {
				doValidation();
			}
		},
		[wasValidated, doValidation]
	);

	const startLoadingToast = () => {
		const toastId = toast.loading("Loading...");
		return toastId;
	};

	const handleSubmission = async function (e) {
		e.preventDefault();
		let toastId = startLoadingToast();
		let form = e.target;
		let formData = new FormData(form);

		console.log(formData);

		let addNew = formData.get("id") === "";

		setWasValidated(true);
		let formValid = doValidation();
		if (!formValid) {
			toast.error("Error in submission", {
				id: toastId,
			});
			return;
		}

		for (let [key, value] of formData.entries()) {
			if (value === "" && !JSONFields.includes(key)) {
				formData.delete(key);
			}
		}

		console.log("Add new :" + addNew);
		console.log(formData);

		let objData = Object.fromEntries(formData);
		for (let key of JSONFields) {
			console.log(objData[key]);
			objData[key] = JSON.parse(objData[key] as string);
		}

		console.log(objData);
		let response;
		if (!addNew) {
			response = await doPatch.mutateAsync({
				apiURL: `${objectType}/${formData.get("id")}/`,
				newData: objData,
			});
		} else {
			response = await doPost.mutateAsync({
				apiURL: `${objectType}/`,
				newData: objData,
			});
		}

		console.log(response);

		if (!response["ok"]) {
			formValid = doValidation(response);
			toast.error(
				`Error in submission ${
					response["detail"] ? ":" + response["detail"] : ""
				}`,
				{
					id: toastId,
				}
			);
			return;
		} else if (addNew) {
			toast.success(`${objectType} succesfully added`, {
				id: toastId,
			});
		} else {
			toast.success(`${objectType} succesfully edited`, {
				id: toastId,
			});
		}

		if (stopEdit) {
			onSubmit(e, addNew, response);
		} else if (addNew) {
			handleReset();
		} else if (!addNew) {
			selectedData = response;
		}
	};

	const handleReset = () => {
		setManagers_ID([]);
		setAnnotators_ID([]);
		setViewers_ID([]);
		onReset();
	};

	const newPATCH = async function (x: { apiURL: string; newData: object }) {
		let response_json = await patchData(x.apiURL, authTokens.access, x.newData);
		//console.log(response_json);
		return response_json;
	};

	const doPatch = useMutation({
		mutationFn: (inputValue: { apiURL: string; newData: object }) =>
			newPATCH(inputValue),
	});

	const newPOST = async function (x: { apiURL: string; newData: object }) {
		let response_json = await postData(x.apiURL, authTokens.access, x.newData);
		//console.log(response_json);
		return response_json;
	};

	const doPost = useMutation({
		mutationFn: (inputValue: { apiURL: string; newData: object }) =>
			newPOST(inputValue),
	});

	const permissionEditor = () => {
		if (
			!selectedData ||
			Object.keys(selectedData as object).includes("managers_ID")
		) {
			return (
				<div className="px-3 py-1 mb-3 border rounded">
					<div className="mb-1">Manage permissions</div>
					<div className="row gy-1 mb-2">
						<div className="col-md-4">
							<PermissionEditor
								permissionName="Managers"
								permissionUsers={managers_ID}
								onPermissionChange={setManagers_ID}
							/>
						</div>
						<div className="col-md-4">
							<PermissionEditor
								permissionName="Annotators"
								permissionUsers={annotators_ID}
								onPermissionChange={setAnnotators_ID}
							/>
						</div>
						<div className="col-md-4">
							<PermissionEditor
								permissionName="Viewers"
								permissionUsers={viewers_ID}
								onPermissionChange={setViewers_ID}
							/>
						</div>
					</div>
				</div>
			);
		}
	};

	return (
		<div>
			<Form
				id="detailForm"
				noValidate
				className={`${wasValidated ? "form-validated" : ""}`}
				onChange={handleFormChange}
				onSubmit={handleSubmission}
				ref={formRef}
			>
				<input
					name="id"
					className="d-none"
					id="post-id"
					value={selectedData ? selectedData["id"] : ""}
					readOnly={true}
				/>

				{children}

				{permissionEditor()}

				<div className="row gy-1 mb-2">
					<div className="col-md-4">
						<button
							name="saveStopButton"
							className="btn btn-primary btn-lg w-100"
							type="submit"
							onClick={(e) => {
								setStopEdit(true);
							}}
						>
							Save
						</button>
					</div>
					<div className="col-md-4">
						<button
							name="saveContinueButton"
							className="btn btn-primary btn-lg w-100"
							type="submit"
							onClick={(e) => {
								setStopEdit(false);
							}}
						>
							Save and keep editing
						</button>
					</div>
					<div className="col-md-4">
						<button
							name="cancelButton"
							className="btn btn-danger btn-lg w-100"
							onClick={onCancel}
						>
							Cancel
						</button>
					</div>
				</div>
			</Form>
		</div>
	);
};

export default DetailEditForm;
