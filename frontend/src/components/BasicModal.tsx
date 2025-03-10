import React, { ReactElement } from "react";
import "../styles/detailmodal.css";

interface Props {
	modalShow: boolean;
	children: ReactElement;
	headerChildren: ReactElement | string;
	onClose: () => void;
}

const BasicModal = ({
	modalShow,
	children,
	headerChildren,
	onClose,
}: Props) => {
	//$el.scrollTo({top: 0, behavior: 'instant'}

	const onBackGroundClick = function (e) {
		if (e.currentTarget !== e.target) return;
		onClose();
	};

	const getHeader = function () {
		if (typeof headerChildren == "string") {
			return <div className="modal-header">{headerChildren}</div>;
		} else {
			return headerChildren;
		}
	};

	const showModal = function () {
		if (modalShow) {
			return (
				<div
					id="detail-modal"
					className="modal"
					role="dialog"
					onClick={onBackGroundClick}
				>
					<div className="modal-dialog modal-lg detail-modal">
						<div className="modal-content shadow">
							{getHeader()}
							<div className="modal-body py-1">{children}</div>
						</div>
					</div>
				</div>
			);
		} else {
			return null;
		}
	};

	return showModal();
};

export default BasicModal;
