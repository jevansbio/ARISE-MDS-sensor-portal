import React from "react";
import DetailDisplayTable from "./DetailDisplayTable.tsx";
import DetailDisplayRelated from "./DetailDisplayRelated.tsx";
import DetailDisplayParents from "./DetailDisplayParents.tsx";
import DetailDisplayFile from "./DetailDisplayFile.tsx";
import FavouriteButton from "./FavouriteButton.tsx";
import DetailDisplayMetrics from "./DetailDisplayMetrics.tsx";

interface Props {
	objectType: string;
	selectedData: object;
}

const DetailDisplay = ({ objectType, selectedData }: Props) => {
	let jsonKeys = ["extra_data"];
	let timeKeys = ["created_on", "modified_on"];
	let displayKeys;

	if (objectType === "deployment") {
		displayKeys = [
			"deployment_device_ID",
			"is_active",
			"deployment_start",
			"deployment_end",
			"time_zone",
			"device",
			"site",
			"latitude",
			"longitude",
			"extra_data",
			"created_on",
			"modified_on",
		];
		timeKeys = timeKeys.concat(["deployment_start", "deployment_end"]);
	} else if (objectType === "device") {
		displayKeys = [
			"device_ID",
			"name",
			"type",
			"model",
			"is_active",
			"username",
			"extra_data",
			"created_on",
			"modified_on",
		];
	} else if (objectType === "project") {
		displayKeys = [
			"project_ID",
			"name",
			"objectives",
			"principal_investigator",
			"principal_investigator_email",
			"contact",
			"contact_email",
			"organisation",
			"created_on",
			"modified_on",
		];
	} else if (objectType === "datafile") {
		displayKeys = [
			"file_name",
			"file_format",
			"recording_dt",
			"deployment",
			"upload_dt",
			"extra_data",
			"file_size",
			"original_name",
			"created_on",
			"modified_on",
		];
		timeKeys = timeKeys.concat(["recording_dt", "upload_dt"]);
	}

	//"recording_dt"

	return (
		<div>
			{objectType === "datafile" ? (
				<>
					<DetailDisplayFile
						fileName={selectedData["file_name"]}
						fileURL={"/" + selectedData["file_url"]}
						fileFormat={selectedData["file_format"]}
					/>
					<FavouriteButton
						id={selectedData["id"]}
						favourite={selectedData["favourite"]}
					/>
				</>
			) : (
				<DetailDisplayMetrics
					id={selectedData["id"]}
					objectType={objectType}
				/>
			)}

			<DetailDisplayRelated
				objectType={objectType}
				selectedDataID={(selectedData as object)["id"] as number}
			/>
			<DetailDisplayParents
				objectType={objectType}
				selectedData={selectedData}
			/>
			<DetailDisplayTable
				selectedData={selectedData}
				displayKeys={displayKeys}
				timeKeys={timeKeys}
				jsonKeys={jsonKeys}
			/>
		</div>
	);
};

DetailDisplay.propTypes = {};

export default DetailDisplay;
