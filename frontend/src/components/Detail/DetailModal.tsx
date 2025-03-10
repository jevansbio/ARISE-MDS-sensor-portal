import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import BasicModal from "../BasicModal.tsx";
import DetailModalHeader from "./DetailModalHeader.jsx";
import DetailModalContent from "./DetailModalContent.tsx";

interface Props {
	data: { results: Object[]; count: number };
	closeDetail: () => void;
	onDetailCancel: (detailNum: number) => void;
	openDetail: (index: number) => void;
	changePage: (newPage) => void;
	setEdit: (editOn: boolean) => void;
	deleteItem: (objId: number) => void;
	onDetailSubmit: (e, addNewBool, response) => void;

	nameKey: string;
	objectType: string;
	pageNum: number;
	isLoading: boolean;
}

const DetailModal = ({
	data,
	closeDetail,
	openDetail,
	changePage,
	setEdit,
	deleteItem,
	onDetailSubmit,
	onDetailCancel,
	isLoading,
	pageNum,
	nameKey,
	objectType,
}: Props) => {
	const [searchParams, setSearchParams] = useSearchParams();
	const modalShow = searchParams.get("detail") && data ? true : false;
	const navigate = useNavigate();
	if (!modalShow) {
		return null;
	}
	const detailNum = Number(searchParams.get("detail"));
	let selectedData;

	let maxPage;
	let maxData;

	let canEdit = true;
	let canDelete = false;

	if (detailNum !== null && detailNum >= 0) {
		selectedData = data.results[detailNum];
		maxPage = Math.ceil(data.count / Number(searchParams.get("page_size")));
		maxData = data.results.length;
		canEdit = selectedData["user_is_manager"];
		canDelete = selectedData["user_is_owner"];
	} else {
		selectedData = null;
		maxPage = null;
		maxData = null;
	}

	let editMode = searchParams.get("edit") && canEdit ? true : false;

	return (
		<BasicModal
			modalShow={modalShow}
			onClose={closeDetail}
			headerChildren={
				<DetailModalHeader
					detailNum={detailNum}
					pageNum={pageNum}
					maxPage={maxPage}
					maxDetail={maxData}
					handleDetailChange={openDetail}
					handlePageChange={changePage}
					isLoading={isLoading}
					editMode={editMode}
					canEdit={canEdit}
					canDelete={canDelete}
					handleEdit={setEdit}
					handleDelete={
						selectedData
							? () => {
									deleteItem(selectedData["id"]);
							  }
							: () => {}
					}
				>
					{selectedData ? selectedData[nameKey] : `Add new ${objectType}`}

					{selectedData ? (
						<a
							className="btn btn-outline-light paginator-button modal-title"
							aria-label="Go to page"
							onClick={() => {
								navigate(`/${objectType}s/${selectedData["id"]}`);
							}}
						>
							Open in new page
						</a>
					) : null}
				</DetailModalHeader>
			}
		>
			<DetailModalContent
				objectType={objectType}
				editMode={editMode}
				selectedData={selectedData}
				onSubmit={onDetailSubmit}
				onCancel={(e) => {
					onDetailCancel(detailNum);
				}}
			/>
		</BasicModal>
	);
};

export default DetailModal;
