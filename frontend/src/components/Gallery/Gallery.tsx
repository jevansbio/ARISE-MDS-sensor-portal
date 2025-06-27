import React from "react";
import { useState, useEffect, useContext, useCallback } from "react";
import { deleteData, getData } from "../../utils/FetchFunctions.js";
import AuthContext from "../../context/AuthContext.jsx";
import GalleryForm from "./GalleryForm.tsx";
import GalleryDisplay from "./GalleryDisplay.tsx";
import GalleryPageControls from "./GalleryPageControls.tsx";

import Loading from "../General/Loading.tsx";
import { useQuery, keepPreviousData, useMutation } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";

import DetailModal from "../Detail/DetailModal.tsx";

import { ObsEditModeContext } from "../../context/ObsModeContext.jsx";
import JobModal from "./JobModal.tsx";
import { useObjectType } from "../../context/ObjectTypeCheck.tsx";

interface GalleryType {
	fromID?: string;
	fromObject?: string;
	objectType?: string;
	nameKey?: string;
}

const Gallery = ({ fromID, fromObject, objectType, nameKey }: GalleryType) => {
	const {
		fromID: contextFromID,
		fromObject: contextFromObject,
		objectType: contextObjectType,
		nameKey: contextNameKey,
	} = useObjectType();

	fromID = fromID ?? contextFromID;
	fromObject = fromObject ?? contextFromObject;
	objectType = objectType ?? contextObjectType;
	nameKey = nameKey ?? contextNameKey;

	if (!nameKey) {
		nameKey = "";
	}

	const defaultPageSize = 30;
	const [searchParams, setSearchParams] = useSearchParams();
	const [formKeys, setFormKeys] = useState<String[]>([]);
	const [pageNum, setPageNum] = useState(Number(searchParams.get("page")) || 1);
	const [pageSize, setPageSize] = useState(
		Number(searchParams.get("page_size")) || defaultPageSize
	);
	const { authTokens, user } = useContext(AuthContext);
	const [obsEditMode, setObsEditMode] = useState(false);
	const [showJobModal, setShowJobModal] = useState(false);
	const [jobID, setJobName] = useState<string | null>(null);
	const [selectedIndexes, setSelectedIndexes] = useState<number[]>([]);

	let additionalOrdering;
	let defaultOrdering = nameKey;
	let defaultTableMode = true;

	if (objectType === "device") {
		additionalOrdering = [{ value: "name", label: "Device name alphabetical" }];
	} else if (objectType === "deployment") {
		additionalOrdering = [
			{ value: "deploymentStart", label: "Deployment start time" },
		];
		defaultTableMode = false;
	} else if (objectType === "datafile") {
		defaultOrdering = "-recording_dt";
		additionalOrdering = [
			{ value: "recording_dt", label: "Recording datetime ascending" },
			{ value: "-recording_dt", label: "Recording datetime descending" },
		];
		defaultTableMode = false;
	} else if (objectType === "project") {
		additionalOrdering = [];
	}

	const [tableMode, setTableMode] = useState(defaultTableMode);

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
		updateSearchParameters("page", pageNum);
	}, [pageNum, updateSearchParameters]);

	useEffect(() => {
		updateSearchParameters("page_size", pageSize);
	}, [pageSize, updateSearchParameters]);

	useEffect(() => {
		updateSearchParameters("ordering", orderBy);
	}, [orderBy, updateSearchParameters]);

	const getDataFunc = async (currentSearchParams) => {
		let apiURL = `${objectType}${fromObject ? `/${fromObject}` : ""}
		${fromID ? `/${fromID}` : ""}
		/?${currentSearchParams.toString()}`;
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
		queryKey: [objectType, user, pageNum, checkSearchParameters().toString()],
		queryFn: () => getDataFunc(searchParams),
		enabled: searchParams.size > 0,
		placeholderData: keepPreviousData,
		refetchOnWindowFocus: false,
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
		// for (let key of searchParams.keys()) {
		// 	if (key === "page") {
		// 		searchParams.set(key, (1).toString());
		// 	} else if (key === "page_size") {
		// 		// Do we need to reset this?
		// 		searchParams.set(key, defaultPageSize.toString());
		// 	}
		// }
		setPageNum(1);
		searchParams.set("page", (1).toString());

		setSearchParams(searchParams);
	};

	const removeSearchParameters = useCallback(
		function (key) {
			let oldSearchParams = searchParams;
			oldSearchParams.delete(key);
			setSearchParams(oldSearchParams);
		},
		[searchParams, setSearchParams]
	);

	const onSubmit = function () {
		setPageNum(1);
	};

	const changePage = useCallback(
		function (newPage) {
			setPageNum(newPage);
		},
		[setPageNum]
	);

	const openDetail = useCallback(
		function (index) {
			updateSearchParameters("detail", index);
		},
		[updateSearchParameters]
	);

	useEffect(() => {
		const handleKeyDown = (e: KeyboardEvent) => {
			if (e.key === "Escape") {
				setSelectedIndexes([]);
			}
		};

		window.addEventListener("keydown", handleKeyDown);
		return () => {
			window.removeEventListener("keydown", handleKeyDown);
		};
	}, []);

	const handleClick = useCallback(
		function (e: React.MouseEvent<Element, MouseEvent>, index: number) {
			if (e.ctrlKey || e.metaKey) {
				setSelectedIndexes((prev) => {
					if (prev.includes(index)) {
						return prev.filter((i) => i !== index);
					} else {
						return [...prev, index];
					}
				});
			} else if (e.shiftKey) {
				document.getSelection()?.removeAllRanges();
				setSelectedIndexes((prev) => {
					if (prev.length > 0) {
						const lastIndex = prev[prev.length - 1];
						const range = [lastIndex, index].sort((a, b) => a - b);
						const newIndexes = Array.from(
							{ length: range[1] - range[0] + 1 },
							(_, i) => range[0] + i
						);
						return Array.from(new Set([...prev, ...newIndexes]));
					} else {
						return [index];
					}
				});
			} else {
				setSelectedIndexes([]);
				openDetail(index);
			}
		},
		[openDetail, setSelectedIndexes]
	);

	const closeDetail = useCallback(
		function () {
			removeSearchParameters("detail");
		},
		[removeSearchParameters]
	);

	const setEdit = useCallback(
		function (editOn = true) {
			if (editOn) {
				updateSearchParameters("edit", editOn);
			} else {
				removeSearchParameters("edit");
			}
		},
		[removeSearchParameters, updateSearchParameters]
	);

	const addNew = useCallback(
		function () {
			setEdit(true);
			openDetail(-1);
		},
		[openDetail, setEdit]
	);

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
					tableMode={tableMode}
					handleChangePage={changePage}
					handleChangePageSize={setPageSize}
					handleChangeOrdering={setOrderBy}
					handleChangeTableDisplay={setTableMode}
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
						onClick={handleClick}
						tableMode={tableMode}
						selectedIndexes={selectedIndexes}
						nameKey={nameKey}
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

	if (objectType === undefined) {
		return null;
	}

	return (
		<div>
			<title>{`Search ${objectType}s`}</title>

			<h3>
				Search {fromID === undefined ? "" : `${fromObject} ${fromID} `}
				{objectType}s
			</h3>
			{showJobModal && data && data.results && data.results.length > 0 ? (
				<JobModal
					jobID={jobID}
					show={showJobModal}
					objectType={objectType}
					fromObject={fromObject}
					fromObjectID={fromID}
					jobPKs={
						selectedIndexes.length > 0
							? selectedIndexes.map((index) => data.results[index]?.id)
							: []
					}
					onClose={() => {
						setShowJobModal(false);
					}}
					key={jobID}
				/>
			) : null}
			<ObsEditModeContext.Provider value={{ obsEditMode, setObsEditMode }}>
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
			</ObsEditModeContext.Provider>
			<GalleryForm
				onSubmit={onSubmit}
				onReset={handleReset}
				pageSize={pageSize}
				pageNum={pageNum}
				orderBy={orderBy ? orderBy : ""}
				setFormKeys={setFormKeys}
				addNew={addNew}
				jobID={jobID}
				onJobChange={setJobName}
				handleStartJob={() => {
					if (jobID !== null) setShowJobModal(true);
				}}
				objectType={objectType}
				fromObject={fromObject}
				fromID={fromID}
				key={`${objectType}-${fromObject}-${fromID}`}
				selectedItemsCount={selectedIndexes.length}
				noData={
					isLoading ||
					data === undefined ||
					(data && data.results && data.results.length === 0)
				}
			/>
			{showGallery()}
		</div>
	);
};

export default Gallery;
