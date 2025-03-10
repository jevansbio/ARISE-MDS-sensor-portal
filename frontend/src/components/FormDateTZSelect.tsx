import React, { useState, ChangeEvent, ChangeEventHandler } from "react";
import FormSelectTZ from "./FormSelectTZ.tsx";
import FormDateSelector from "./FormDateSelector.tsx";
import { itemFromTimeZone } from "../utils/timezoneFunctions.js";
import { fromZonedTime, formatInTimeZone } from "date-fns-tz";

interface Props {
	id: string;
	name: string;
	label: string;
	text: string;
	defaultvalue?: string;
	handleChange?: ChangeEventHandler<HTMLInputElement>;
	validated?: boolean;
	valid?: boolean;
	required?: boolean;
}

const FormDateTZSelect = ({
	id,
	name,
	label,
	text,
	defaultvalue,
	handleChange,
	validated = false,
	valid = true,
	required = false,
}: Props) => {
	const [timeZone, setTimeZone] = useState(
		itemFromTimeZone(Intl.DateTimeFormat().resolvedOptions().timeZone).value
	);
	const [dateTime, setDateTime] = useState(
		defaultvalue
			? formatInTimeZone(defaultvalue, timeZone, "yyyy-MM-dd'T'HH:mm:ss")
			: ""
	);

	const [dateTimeString, setDateTimeString] = useState(
		defaultvalue ? defaultvalue : ""
	);

	const setTimeZoneFromField = function (newValue) {
		setTimeZone(newValue);

		setDateTimeString(fromZonedTime(dateTime, newValue).toJSON());
	};

	const setDateTimeFromField = function (e: ChangeEvent<HTMLInputElement>) {
		if (!e.target) return;
		let target = e.target as HTMLInputElement;
		let newValue = target.value;
		setDateTime(newValue);
		setDateTimeString(fromZonedTime(newValue, timeZone).toJSON());
	};

	return (
		<div
			id={id}
			className="row"
		>
			<div className="col-md-7 pe-md-0">
				<FormDateSelector
					id={`${id}_dt`}
					name={`${name}_dt`}
					label={label}
					handleChange={setDateTimeFromField}
					defaultvalue={dateTime}
					valid={valid}
					validated={validated}
					float={false}
				/>
			</div>
			<div className="col-md-5 ps-md-0">
				<FormSelectTZ
					id={`${id}_TZ`}
					name={`${name}_TZ`}
					label="Timezone"
					handleChange={setTimeZoneFromField}
					value={timeZone}
					valid={valid}
				/>
			</div>

			{required ? (
				<input
					id={`${id}_UTC`}
					name={name}
					value={dateTimeString}
					className="d-none"
					onChange={handleChange}
					required
				/>
			) : (
				<input
					id={`${id}_UTC`}
					name={name}
					value={dateTimeString}
					className="d-none"
					onChange={handleChange}
				/>
			)}
		</div>
	);
};

export default FormDateTZSelect;
