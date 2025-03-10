import React, { ChangeEvent } from "react";
import "../styles/base.css";

interface Props {
	id: string;
	name: string;
	label: string;
	defaultvalue?: string;
	className?: string;
	handleChange?: (e: ChangeEvent<HTMLInputElement>) => void;
	valid?: boolean;
	validated?: boolean;
	float?: boolean;
}

const FormDateSelector = ({
	id,
	name,
	label,
	defaultvalue,
	className = "",
	handleChange = (e) => {},
	valid = true,
	validated = false,
	float = true,
}: Props) => {
	return (
		<div className={`${float ? "form-floating" : ""} ${className}`}>
			<input
				className={`form-control px-1 ${
					validated ? (valid ? "is-valid" : "is-invalid") : ""
				}`}
				type="datetime-local"
				id={id}
				name={name}
				defaultValue={defaultvalue}
				onChange={handleChange}
			/>
			{float ? <label htmlFor={id}>{label}</label> : ""}
		</div>
	);
};

export default FormDateSelector;
