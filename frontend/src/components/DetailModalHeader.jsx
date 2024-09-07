import React from "react";
import "../styles/base.css";
import Loading from "./Loading.tsx";

const DetailModalHeader = (props) => {
	const changeDetail = function (change) {
		let newDetail = Number(props.detailNum) + change;
		newDetail = setDetail(newDetail);
	};

	const setDetail = function (newDetail) {
		if (newDetail >= 0 && newDetail < Number(props.maxDetail)) {
			props.handleDetailChange(newDetail);
		} else if (newDetail >= Number(props.maxDetail)) {
			let pageChange = changePage(1);
			if (pageChange) {
				newDetail = 0;
				props.handleDetailChange(newDetail);
			}
		} else if (newDetail < 0) {
			let pageChange = changePage(-1);
			if (pageChange) {
				newDetail = Number(props.maxDetail) - 1;
				props.handleDetailChange(newDetail);
			}
		}
		console.log(newDetail);
	};

	const changePage = function (change) {
		console.log("new page");
		console.log(Number(props.pageNum));
		let newPage = Number(props.pageNum) + change;
		let pageChange = setPage(newPage);
		return pageChange;
	};

	const setPage = function (newPage) {
		console.log("set page");
		console.log(newPage);
		if (newPage >= 1 && newPage <= Number(props.maxPage)) {
			props.handlePageChange(newPage);
			return true;
		} else if (newPage < 1) {
			newPage = 1;
			return false;
		} else if (newPage > Number(props.maxPage)) {
			newPage = props.maxPage;
			return false;
		}
	};

	const handleEdit = function (e) {
		console.log("edit button clicked");
		props.handleEdit(true);
	};

	const getEnabled = function (left = true) {
		if (left) {
			if (Number(props.pageNum) <= 1 && props.detailNum <= 0) {
				return "disabled";
			} else {
				return "";
			}
		} else {
			if (
				Number(props.pageNum) >= props.maxPage &&
				props.detailNum >= props.maxDetail - 1
			) {
				return "disabled";
			} else {
				return "";
			}
		}
	};

	return (
		<div className="modal-header">
			<a
				className={`btn btn-outline-light paginator-button modal-title ${getEnabled(
					true
				)}`}
				aria-label="Previous"
				onClick={(e) => changeDetail(-1)}
			>
				<h5
					className="paginator-arrow"
					aria-hidden="true"
				>
					&laquo;
				</h5>
			</a>

			<h5
				className="modal-title"
				id="detailTitle"
			>
				{props.children}
				<a className="text-reset text-decoration-none"></a>
			</h5>
			{props.editMode ? null : (
				<a
					className="btn btn-outline-light paginator-button modal-title"
					aria-label="Edit"
					onClick={handleEdit}
				>
					Edit
				</a>
			)}
			<Loading
				enabled={props.isLoading}
				large={false}
				showText={false}
			/>
			<a
				className={`btn btn-outline-light paginator-button modal-title last-item ${getEnabled(
					false
				)}`}
				aria-label="Next"
				onClick={(e) => changeDetail(1)}
			>
				<h5
					className="paginator-arrow"
					aria-hidden="true"
				>
					&raquo;
				</h5>
			</a>
		</div>
	);
};

export default DetailModalHeader;
