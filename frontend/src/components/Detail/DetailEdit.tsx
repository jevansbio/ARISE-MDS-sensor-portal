import React, { useState } from "react";
import DetailEditDeployment from "./DetailEditDeployment.tsx";
import DetailEditDevice from "./DetailEditDevice.tsx";
import DetailEditProject from "./DetailEditProject.tsx";

interface Props {
	objectType: string;
	selectedData?: object | null;
	onSubmit?: (e: Event, addNew: boolean, response: object) => void;
	onCancel?: (e: any) => void;
}

const DetailEdit = ({
	objectType,
	selectedData,
	onSubmit,
	onCancel,
}: Props) => {
	const [wasValidated, setWasValidated] = useState(false);
	const [errorDict, setErrorDict] = useState({});

	const resetForm = () => {
		setWasValidated(false);
		setErrorDict({});
	};

	const getForm = () => {
		if (objectType === "deployment") {
			return (
				<DetailEditDeployment
					selectedData={selectedData}
					onSubmit={onSubmit}
					onCancel={onCancel}
					setErrorDict={setErrorDict}
					setWasValidated={setWasValidated}
					wasValidated={wasValidated}
					errorDict={errorDict}
					onReset={resetForm}
				/>
			);
		} else if (objectType === "device") {
			return (
				<DetailEditDevice
					selectedData={selectedData}
					onSubmit={onSubmit}
					onCancel={onCancel}
					setErrorDict={setErrorDict}
					setWasValidated={setWasValidated}
					wasValidated={wasValidated}
					errorDict={errorDict}
					onReset={resetForm}
				/>
			);
		} else if (objectType === "project") {
			return (
				<DetailEditProject
					selectedData={selectedData}
					onSubmit={onSubmit}
					onCancel={onCancel}
					setErrorDict={setErrorDict}
					setWasValidated={setWasValidated}
					wasValidated={wasValidated}
					errorDict={errorDict}
					onReset={resetForm}
				/>
			);
		}
	};

	return getForm();
};

export default DetailEdit;
