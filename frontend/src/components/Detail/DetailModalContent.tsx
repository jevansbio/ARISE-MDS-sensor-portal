import React from "react";
import DetailEdit from "./DetailEdit.tsx";
import DetailDisplay from "./DetailDisplay.tsx";

interface Props {
	objectType: string;
	editMode: boolean;
	selectedData: object | null;
	onSubmit?: (e: Event, addNew: boolean, response: object) => void;
	onCancel?: (e: any) => void;
}

const DetailModalContent = ({
	objectType,
	editMode,
	selectedData,
	onSubmit = (e, addNew, response) => {},
	onCancel = () => {},
}: Props) => {
	if (selectedData) {
		if (!selectedData["user_is_manager"]) {
			editMode = false;
		}
	}

	return editMode ? (
		<DetailEdit
			objectType={objectType}
			selectedData={selectedData}
			onSubmit={onSubmit}
			onCancel={onCancel}
		/>
	) : (
		<DetailDisplay
			objectType={objectType}
			selectedData={selectedData}
		/>
	);
};

export default DetailModalContent;
