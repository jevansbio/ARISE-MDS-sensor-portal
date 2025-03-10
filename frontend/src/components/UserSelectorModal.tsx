import React, { useState } from "react";
import BasicModal from "./BasicModal.tsx";
import UserSelector from "./UserSelector.tsx";

interface Props {
	permissionname: string;
	chosenUsers: Number[];
	onPermissionChange: (number, boolean) => void;
}

const UserSelectorModal = ({
	permissionname,
	chosenUsers,
	onPermissionChange,
}: Props) => {
	const [modalOpen, setModalOpen] = useState(false);

	return (
		<>
			<button
				className={`w-100 btn btn-secondary ${modalOpen ? "disabled" : ""}`}
				disabled={modalOpen}
				onClick={
					modalOpen
						? () => {}
						: (e) => {
								setModalOpen(true);
						  }
				}
			>
				{permissionname}
			</button>

			{modalOpen ? (
				<BasicModal
					modalShow={modalOpen}
					children={
						<div className="p-2">
							<div>
								<UserSelector
									chosenUsers={chosenUsers}
									onPermissionChange={onPermissionChange}
								/>
							</div>
							<div className="pt-3 d-flex justify-content-center">
								<button
									className="btn btn-secondary w-50"
									onClick={() => setModalOpen(false)}
								>
									Close
								</button>
							</div>
						</div>
					}
					headerChildren={
						<div className="modal-header p-1">Edit {permissionname}</div>
					}
					onClose={() => {
						setModalOpen(false);
					}}
				/>
			) : null}
		</>
	);
};

export default UserSelectorModal;
