import React from "react";
import UserSelectorModal from "./UserSelectorModal.tsx";

interface Props {
	permissionName: string;
	permissionUsers: number[];
	onPermissionChange: (newValue) => void;
}

const PermissionEditor = ({
	permissionName,
	permissionUsers,
	onPermissionChange,
}: Props) => {
	return (
		<>
			<UserSelectorModal
				permissionname={permissionName}
				chosenUsers={permissionUsers}
				onPermissionChange={onPermissionChange}
			/>
			<input
				name={`${permissionName.toLowerCase()}_ID`}
				value={JSON.stringify(permissionUsers)}
				hidden
			></input>
		</>
	);
};

export default PermissionEditor;
