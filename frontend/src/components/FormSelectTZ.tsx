import React, { ChangeEvent } from "react";
import FormSelect from "./FormSelect.tsx";
import { timezonesWithoffsets } from "../utils/timezoneFunctions.js";

interface Props {
	name: string;
	id: string;
	label: string;
	className?: string;
	value?: string;
	handleChange?: (e: ChangeEvent<HTMLInputElement>) => void;
	valid?: boolean;
}

const FormSelectTZ = ({
	name,
	id,
	label,
	className,
	value,
	handleChange = () => {},
	valid = true,
}: Props) => {
	return (
		<FormSelect
			value={value}
			name={name}
			id={id}
			label={label}
			choices={timezonesWithoffsets}
			isClearable={false}
			multiple={false}
			handleChange={handleChange}
			valid={valid}
		/>
	);
};

export default FormSelectTZ;
