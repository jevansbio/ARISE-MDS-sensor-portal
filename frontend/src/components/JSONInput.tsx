import React, { useState, useEffect, Dispatch } from "react";

interface Props {
	name?: string;
	id?: string;
	value?: object;
	onJSONchange?: Dispatch<object>;
	showTextField?: boolean;
	wasValidated?: boolean;
	errorDict?: object;
}

const JSONInput = ({
	name = "JSONinfo",
	id = "JSONinfo",
	value = {},
	onJSONchange = (e) => {},
	showTextField = false,
	wasValidated = false,
	errorDict = {},
}: Props) => {
	const [JSONtext, setJSONtext] = useState(JSON.stringify(value));
	const [inputFields, setInputFields] = useState(
		Object.entries(value).map(([key, value]) => {
			return { key: key, value: value };
		})
	);

	const handleFormChange = (index, event) => {
		let data = [...inputFields];
		data[index][event.target.name] = event.target.value;
		setInputFields(data);
	};

	const addFields = (e) => {
		e.preventDefault();
		let newfield = { key: "", value: "" };
		setInputFields([...inputFields, newfield]);
	};

	const removeFields = (index) => {
		let data = [...inputFields];
		data.splice(index, 1);
		setInputFields(data);
	};

	useEffect(() => {
		let newObj = inputFields.reduce(
			(obj, item) => ({ ...obj, [item.key]: item.value }),
			{}
		);
		let newJSONstring = JSON.stringify(newObj);
		setJSONtext(newJSONstring);
		console.log(newObj);
		onJSONchange(newObj);
	}, [inputFields, onJSONchange]);

	return (
		<div className={"my-1"}>
			<textarea
				name={name}
				id={id}
				value={JSONtext}
				readOnly={true}
				className={showTextField ? "form-control" : "d-none"}
			></textarea>

			{inputFields.map((input, index) => {
				return (
					<div
						key={index}
						className="row pt-1"
					>
						<div className={"col-4 pe-1"}>
							<input
								className={`form-control ${
									wasValidated
										? errorDict[input.key]
											? "is-invalid"
											: "is-valid"
										: ""
								}`}
								name="key"
								placeholder="key"
								value={input.key}
								form=""
								onChange={(event) => handleFormChange(index, event)}
							/>
						</div>
						<div className={"col-auto px-0"}>
							<p className={"form-control-plaintext "}>:</p>
						</div>
						<div className={"col-4 px-1"}>
							<input
								className={`form-control ${
									wasValidated
										? errorDict[input.key]
											? "is-invalid"
											: "is-valid"
										: ""
								}`}
								name="value"
								placeholder="value"
								value={input.value}
								form=""
								onChange={(event) => handleFormChange(index, event)}
							/>
						</div>
						<div className={"col-2 px-1"}>
							<button
								className="btn btn-danger"
								onClick={(e) => {
									e.preventDefault();
									removeFields(index);
								}}
							>
								Remove
							</button>
						</div>
					</div>
				);
			})}
			<div className="row g-1 my-1">
				<button
					onClick={addFields}
					className="btn btn-secondary"
				>
					Add More..
				</button>
			</div>
		</div>
	);
};

export default JSONInput;
