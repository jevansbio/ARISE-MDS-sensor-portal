import React from "react";
import { useState, useEffect, useContext, useCallback } from "react";
import { deleteData, getData } from "../../utils/FetchFunctions.js";
import AuthContext from "../../context/AuthContext.jsx";
import GalleryForm from "./GalleryForm.tsx";
import GalleryDisplay from "./GalleryDisplay.tsx";
import GalleryPageControls from "./GalleryPageControls.tsx";

import Loading from "../Loading.tsx";
import { useQuery, keepPreviousData, useMutation } from "@tanstack/react-query";
import { useOutletContext, useParams, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";

import DetailModal from "../Detail/DetailModal.tsx";

const Gallery = () => {
	const { fromID, fromObject, objectType, nameKey } = useOutletContext();
	const defaultPageSize = 28;
	const [searchParams, setSearchParams] = useSearchParams();
	const [formKeys, setFormKeys] = useState<String[]>([]);
	const [pageNum, setPageNum] = useState(Number(searchParams.get("page")) || 1);
	const [pageSize, setPageSize] = useState(
		Number(searchParams.get("page_size")) || defaultPageSize
	);
	const { authTokens, user } = useContext(AuthContext);

	let additionalOrdering;
	let defaultOrdering = nameKey;
	let thumbKey = "";

	if (objectType === "device") {
		additionalOrdering = [{ value: "name", label: "Device name alphabetical" }];
	} else if (objectType === "deployment") {
		additionalOrdering = [
			{ value: "deploymentStart", label: "Deployment start time" },
		];
	} else if (objectType === "datafile") {
		defaultOrdering = "recording_dt";
		additionalOrdering = [
			{ value: "recording_dt", label: "Recording datetime ascending" },
			{ value: "-recording_dt", label: "Recording datetime descending" },
		];
	} else {
		additionalOrdering = [];
	}

	const [orderBy, setOrderBy] = useState(
		searchParams.get("ordering")
			? searchParams.get("ordering")
			: defaultOrdering
	);

	useEffect(() => {
		setPageNum(1);
		setOrderBy(defaultOrdering);
	}, [objectType, defaultOrdering]);

	const updateSearchParameters = useCallback(
		function (key, val) {
			let oldSearchParams = searchParams;
			if (oldSearchParams.size > 0) {
				oldSearchParams.set(key, val);
				setSearchParams(oldSearchParams);
			}
		},
		[searchParams, setSearchParams]
	);

	useEffect(() => {
		console.log(pageNum);
		updateSearchParameters("page", pageNum);
	}, [pageNum, updateSearchParameters]);

	useEffect(() => {
		updateSearchParameters("page_size", pageSize);
	}, [pageSize, updateSearchParameters]);

	useEffect(() => {
		updateSearchParameters("ordering", orderBy);
	}, [orderBy, updateSearchParameters]);

	const getDataFunc = async (currentSearchParams) => {
		let apiURL = `${objectType}/?${currentSearchParams.toString()}`;
		console.log(apiURL);
		let response_json = await getData(apiURL, authTokens.access);
		return response_json;
	};

	const checkSearchParameters = function () {
		let searchParamsObject = Object.fromEntries(searchParams);
		if (formKeys) {
			Object.entries(searchParamsObject).forEach(([key, value]) => {
				if (!formKeys.includes(key)) {
					delete searchParamsObject[key];
				}
			});
		}
		return new URLSearchParams(searchParamsObject);
	};

	const {
		isLoading,
		isError,
		isPending,
		data,
		error,
		isRefetching,
		isPlaceholderData,
		refetch,
	} = useQuery({
		queryKey: ["data", user, checkSearchParameters().toString()],
		queryFn: () => getDataFunc(searchParams),
		enabled: searchParams.size > 0,
		placeholderData: keepPreviousData,
	});

	const newDELETE = async function (objID) {
		let response_json = await deleteData(
			`${objectType}/${objID}`,
			authTokens.access
		);
		return response_json;
	};

	const doDelete = useMutation({
		mutationFn: (objID) => newDELETE(objID),
	});

	const orderingChoices = [
		{
			value: nameKey,
			label: `${nameKey.replace("_", " ")} alphabetical`,
		},
		{ value: "created_on", label: "Registration time" },
		{
			value: "-created_on",
			label: "Registration time (descending)",
		},
	].concat(additionalOrdering);

	const handleReset = function (searchParams) {
		for (let key of searchParams.keys()) {
			if (key === "page") {
				searchParams.set(key, (1).toString());
			} else if (key === "page_size") {
				// Do we need to reset this?
				searchParams.set(key, defaultPageSize.toString());
			} else {
				searchParams.set(key, "");
			}
		}
		console.log(searchParams);
		setSearchParams(searchParams);

		setPageNum(1);

		//perhaps we don't need to reset this?
		setPageSize(defaultPageSize);
		//perhaps we don't need to reset this?
		setOrderBy(defaultOrdering);
	};

	const removeSearchParameters = function (key) {
		let oldSearchParams = searchParams;
		oldSearchParams.delete(key);
		setSearchParams(oldSearchParams);
	};

	const onSubmit = function () {
		setPageNum(1);
	};

	const changePage = function (newPage) {
		console.log(newPage);
		setPageNum(newPage);
	};

	const openDetail = function (index) {
		updateSearchParameters("detail", index);
	};

	const closeDetail = function () {
		console.log("close detail");
		removeSearchParameters("detail");
	};

	const setEdit = function (editOn = true) {
		if (editOn) {
			updateSearchParameters("edit", editOn);
		} else {
			removeSearchParameters("edit");
		}
	};

	const addNew = function () {
		setEdit(true);
		openDetail(-1);
	};

	const showGallery = function () {
		if (isLoading || isPending || isRefetching) {
			return <Loading />;
		}

		if (isError) {
			return <p>An error occurred: {error.message}</p>;
		}
		if (!searchParams.get("page_size")) return;

		let maxPage = Math.ceil(data.count / Number(searchParams.get("page_size")));

		return (
			<div>
				<GalleryPageControls
					pageNum={pageNum}
					pageSize={pageSize}
					maxPage={maxPage}
					orderBy={orderBy ? orderBy : ""}
					orderingChoices={orderingChoices}
					handleChangePage={changePage}
					handleChangePageSize={setPageSize}
					handleChangeOrdering={setOrderBy}
					// change itemsperpage callback
					// change result ordering callback
				/>
				<div
					id="display-container"
					className={`${isPlaceholderData ? "opacity-50" : ""} container`}
				>
					<GalleryDisplay
						objectType={objectType}
						data={data.results}
						onTileClick={openDetail}
					/>
				</div>
			</div>
		);
	};

	const onDetailSubmit = function (e, addNewBool, response) {
		if (!addNewBool) {
			//let detailNum = searchParams.get("detail");
			//data.results[detailNum] = response;
			refetch();
			setEdit(false);
		} else if (addNewBool) {
			updateSearchParameters("ordering", "-created_on");
			setEdit(false);
			closeDetail();
			setPageNum(1);
			refetch();
		}
	};

	const deleteItem = async function (objID) {
		let response = await doDelete.mutateAsync(objID);
		console.log(response);
		if (response["ok"]) {
			toast(`${objectType} deleted`);
			setPageNum(1);
			refetch();
			closeDetail();
		}
	};

	const handleDetailModalCancel = function (detailNum) {
		if (detailNum && detailNum > -1) {
			setEdit(false);
		} else {
			setEdit(false);
			closeDetail();
		}
	};

	return (
		<div>
			<title>{`Search ${objectType}s`}</title>

			<h3>
				Search {fromID === undefined ? "" : `${fromObject} ${fromID} `}
				{objectType}s
			</h3>
			<DetailModal
				data={data}
				closeDetail={closeDetail}
				onDetailCancel={handleDetailModalCancel}
				openDetail={openDetail}
				changePage={changePage}
				setEdit={setEdit}
				deleteItem={deleteItem}
				onDetailSubmit={onDetailSubmit}
				nameKey={nameKey}
				pageNum={pageNum}
				objectType={objectType}
				isLoading={isLoading || isPending ? true : false}
			/>
			<GalleryForm
				onSubmit={onSubmit}
				onReset={handleReset}
				pageSize={pageSize}
				pageNum={pageNum}
				orderBy={orderBy ? orderBy : ""}
				setFormKeys={setFormKeys}
				addNew={addNew}
				nameKey={nameKey}
				objectType={objectType}
				fromObject={fromObject}
				fromID={fromID}
			/>
			{showGallery()}
		</div>
	);
};

export default Gallery;
