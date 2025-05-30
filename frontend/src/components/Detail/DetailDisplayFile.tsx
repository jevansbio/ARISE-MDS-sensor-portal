import React, { useCallback, useContext, useState } from "react";

import RectDraw from "./Observations/RectDraw.tsx";
import FavouriteButton from "./FavouriteButton.tsx";
import { ObsEditModeContext } from "../../context/ObsModeContext.jsx";
import AuthContext from "../../context/AuthContext.jsx";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { getData } from "../../utils/FetchFunctions.js";
import Loading from "../General/Loading.tsx";
import ObservationForm, {
	obsDataType,
} from "./Observations/ObservationForm.tsx";
import ObservationTable from "./Observations/ObservationTable.tsx";

interface Props {
	fileData: Object;
}

const DetailDisplayFile = ({ fileData }: Props) => {
	const { authTokens, user } = useContext(AuthContext);
	const { obsEditMode, setObsEditMode } = useContext(ObsEditModeContext);

	const isImage = [".jpg", ".jpeg", ".png"].includes(
		fileData["file_format"].toLowerCase()
	);
	const fileURL = "/" + fileData["file_url"];
	const canAnnotate = fileData["can_annotate"];

	const [bboxEditMode, setBboxEditMode] = useState({
		edit: false,
		index: -1,
	});
	const [tempObsData, setTempObsData] = useState<obsDataType[]>([]);
	const [hoverIndex, setHoverIndex] = useState(-1);
	const [expanded, setExpanded] = useState(false);

	const handleObservationEdit = useCallback((rowData, newRow = false) => {
		if (newRow) {
			setTempObsData((prevState) => {
				return [...prevState, rowData];
			});
		} else {
			setTempObsData((prevState) => {
				return prevState.map((x, i) => {
					if (i === rowData.index) {
						return rowData;
					} else {
						return x;
					}
				});
			});
		}
	}, []);

	const handleStartEditBoundingBox = useCallback((index) => {
		setBboxEditMode({
			edit: true,
			index: index,
		});
	}, []);

	const handleStopEditBoundingBox = useCallback((newObsData) => {
		setBboxEditMode({
			edit: false,
			index: -1,
		});
		setTempObsData(newObsData);
	}, []);

	const getDataFunc = async () => {
		let apiURL = `observation/?data_files=${fileData["id"]}`;
		let response_json = await getData(apiURL, authTokens.access);
		setTempObsData(response_json);
		return response_json;
	};

	const {
		isLoading,
		//isError,
		isPending,
		data,
		//error,
		isRefetching,
		//isPlaceholderData,
		refetch,
	} = useQuery({
		queryKey: ["obs", user, fileData["id"]],
		queryFn: () => getDataFunc(),
		placeholderData: keepPreviousData,
		refetchOnWindowFocus: false,
	});

	const handleSetEditMode = useCallback(
		(startEdit) => {
			if (!startEdit) {
				refetch();
			}
			setTempObsData(data);
			setObsEditMode(startEdit);
		},
		[data, refetch, setObsEditMode]
	);

	const handleRowHover = useCallback((index) => {
		setHoverIndex(index);
	}, []);

	const getObsTable = () => {
		if (isLoading || isPending || isRefetching) {
			return <Loading />;
		} else {
			return (
				<div>
					{obsEditMode ? (
						<ObservationForm
							allObsData={tempObsData}
							fileData={fileData}
							onSubmit={refetch}
							onEditBoundingBox={handleStartEditBoundingBox}
							onEdit={handleObservationEdit}
							onHover={handleRowHover}
							onStopEdit={() => handleSetEditMode(false)}
						/>
					) : (
						<ObservationTable
							allObsData={data}
							onRowHover={handleRowHover}
						/>
					)}
					{canAnnotate ? (
						<button
							className={`btn ${
								obsEditMode ? "btn-outline-danger" : "btn-outline-primary w-100"
							}`}
							onClick={() => {
								handleSetEditMode(!obsEditMode);
							}}
						>
							{obsEditMode ? "Cancel annotating" : "Start annotating"}
						</button>
					) : null}
				</div>
			);
		}
	};

	return (
		<div>
			<div
				onClick={() => {
					if (isImage && !obsEditMode) {
						setExpanded(!expanded);
					}
				}}
			>
				{isImage ? (
					<div className={"rectdraw-container"}>
						<img
							src={fileURL}
							alt={fileData["file_name"]}
							style={{
								objectFit: "contain",
								width: "100%",
								maxHeight: expanded ? "100%" : "30rem",
								userSelect: "none",
							}}
						/>
						<RectDraw
							obsData={tempObsData}
							editMode={bboxEditMode.edit}
							editIndex={bboxEditMode.index}
							onFinishEditing={handleStopEditBoundingBox}
							hoverIndex={hoverIndex}
						/>
					</div>
				) : (
					<a
						href={fileURL}
						target="_blank'"
					>
						"Download File"
					</a>
				)}
			</div>
			<FavouriteButton
				id={fileData["id"]}
				favourite={fileData["favourite"]}
			/>
			{getObsTable()}
		</div>
	);
};

export default DetailDisplayFile;
