import React from "react";
import { useEffect, useRef, useState } from "react";
import { Form, useOutletContext, useParams } from "react-router-dom";
import FormSelect from "../FormSelect.tsx";
import FormSelectAPI from "../FormSelectAPI.tsx";
import FormDateSelector from "../FormDateSelector.tsx";
import { useSearchParams } from "react-router-dom";

interface Props {
	objectType?: string;
	fromObject?: string;
	fromID?: string;
	onSubmit: () => void;
	addNew: () => void;
	setFormKeys: (val: string[]) => void;
	orderBy: string;
	pageSize: number;
	pageNum: number;
	onReset: (searchParams: any) => void;
}

function GalleryForm({
	onSubmit,
	addNew,
	setFormKeys,
	orderBy,
	pageSize,
	pageNum,
	onReset,
	objectType = "deployment",
	fromObject = undefined,
	fromID = undefined,
}: Props) {
	const [searchParams, setSearchParams] = useSearchParams();

	const formRef = useRef<HTMLFormElement>(null);

	const handleSubmit = function (e) {
		onSubmit();
	};
	const handleAddNew = function (e) {
		e.preventDefault();
		addNew();
	};

	const [isActive, setIsActive] = useState(searchParams.get("is_active"));
	const [site, setSite] = useState(searchParams.get("site"));
	const [deviceType, setDeviceType] = useState(searchParams.get("device_type"));
	const [fileType, setFileType] = useState(searchParams.get("file_type"));

	useEffect(() => {
		if (searchParams.size === 0) {
			if (!formRef.current) return;
			let formData = new FormData(formRef.current);
			console.log(formData);
			setSearchParams(
				new URLSearchParams(formData as unknown as Record<string, string>)
			);
		}
	}, [searchParams, setSearchParams]);

	useEffect(() => {
		if (!formRef.current) return;
		let formData = new FormData(formRef.current);
		setFormKeys(Array.from(formData.keys()));
		console.log(Array.from(formData.keys()));
	}, [formRef, setFormKeys]);

	const resetForm = function (e) {
		e.preventDefault();
		if (!formRef.current) return;
		formRef.current.reset();
		let formData = new FormData(formRef.current);
		console.log(formData);
		let searchParams = new URLSearchParams(
			formData as unknown as Record<string, string>
		);
		onReset(searchParams);

		//Resetting select boxes
		setIsActive(null);
		setSite(null);
		setDeviceType(null);

		//call reset callback
	};

	const activeField = function () {
		if (!["deployment", "device", "project", "datafile"].includes(objectType))
			return;

		return (
			<div className="col-lg-2">
				<div className="form-floating">
					<FormSelect
						id="select-is_active"
						name="is_active"
						label="Deployment active?"
						choices={[
							{ value: "True", label: "True" },
							{ value: "False", label: "False" },
						]}
						isSearchable={false}
						//defaultvalue={searchParams.get("is_active") || null}
						value={isActive}
						handleChange={setIsActive}
					/>
				</div>
			</div>
		);
	};

	const dateField = function (id, name, label, validtypes) {
		if (!validtypes.includes(objectType)) return;

		return (
			<FormDateSelector
				id={id}
				name={name}
				label={label}
				defaultvalue={
					!searchParams.get(name)
						? undefined
						: (searchParams.get(name) as string)
				}
				className="col-lg-2"
			/>
		);
	};

	const siteField = function () {
		if (!["deployment", "device", "datafile"].includes(objectType)) return;

		return (
			<div className="col-lg-2">
				<div className="form-floating">
					<FormSelectAPI
						id="select-site"
						name="site"
						label="Site"
						choices={[]}
						value={site}
						apiURL="site/"
						valueKey="id"
						labelKey="short_name"
						handleChange={setSite}
					/>
				</div>
			</div>
		);
	};

	const deviceTypeField = function () {
		if (!["deployment", "device", "datafile"].includes(objectType)) return;

		return (
			<div className="col-lg-2">
				<div className="form-floating">
					<FormSelectAPI
						key="select-datatype"
						id="select-datatype"
						name="device_type"
						label="Device type"
						choices={[]}
						value={deviceType}
						apiURL="datatype/?device_type=true"
						valueKey="id"
						labelKey="name"
						handleChange={setDeviceType}
					/>
				</div>
			</div>
		);
	};

	const dataFileTypeField = function () {
		if (objectType !== "datafile") return;

		return (
			<div className="col-lg-2">
				<div className="form-floating">
					<FormSelectAPI
						key="select-filetype"
						id="select-fileType"
						name="file_type"
						label="File type"
						choices={[]}
						value={fileType}
						apiURL="datatype/?file_type=true"
						valueKey="id"
						labelKey="name"
						handleChange={setFileType}
					/>
				</div>
			</div>
		);
	};

	const fromObjectFilter = function () {
		if (fromID === undefined) {
			return null;
		} else {
			return (
				<input
					name={fromObject}
					className="d-none"
					id={fromObject}
					defaultValue={fromID}
				/>
			);
		}
	};

	return (
		<div id="search-form-div">
			<Form
				className="mb-3"
				onSubmit={handleSubmit}
				id="search-form"
				ref={formRef}
			>
				<div className="row gx-3 gy-2">
					<div className="col-lg-5">
						<div className="form-floating">
							<input
								name="search"
								id="search"
								className="form-control"
								defaultValue={
									!searchParams.get("search")
										? undefined
										: (searchParams.get("search") as string)
								}
							/>
							<label htmlFor="search">Search</label>
						</div>
					</div>
					{activeField()}
					{siteField()}
					{deviceTypeField()}
					{dataFileTypeField()}
					{dateField(
						"start_date",
						"deployment_start__gte",
						"Deployment started after",
						["deployment"]
					)}
					{dateField(
						"end_date",
						"deployment_end__lte",
						"Deployment ended before",
						["deployment"]
					)}
					{dateField("start_date", "recording_dt__gte", "File recorded after", [
						"datafile",
					])}
					{dateField("end_date", "recording_dt__lte", "File recorded before", [
						"datafile",
					])}

					<div className="d-grid gap-2 d-md-block mt-2 pt-1 col-lg-4">
						<button
							type="submit"
							className="btn btn-primary btn-lg me-lg-2"
						>
							Search
						</button>

						<button
							type="button"
							className="btn btn-danger btn-lg ms-lg-2 me-lg-2"
							onClick={resetForm}
						>
							Reset
						</button>

						<button
							type="button"
							className="btn btn-success btn-lg ms-lg-2"
							onClick={handleAddNew}
						>
							Add new
						</button>
					</div>
				</div>

				<input
					name="page"
					className="d-none"
					type="number"
					value={pageNum}
					readOnly={true}
				/>
				<input
					name="ordering"
					className="d-none"
					value={orderBy}
					readOnly={true}
				/>
				<input
					name="page_size"
					className="d-none"
					type="number"
					value={pageSize}
					readOnly={true}
				/>
				{fromObjectFilter()}
			</Form>
		</div>
	);
}

export default GalleryForm;
