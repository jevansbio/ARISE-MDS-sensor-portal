// Get data from API
export async function getData(url, token) {
	let response = await fetch(`/${import.meta.env.VITE_API_BASE_URL}/${url}`, {
		headers: {
			Authorization: "Bearer " + String(token),
			"Content-Type": "application/json",
		},
	});
	if (!response.ok) {
		throw new Error(response.statusText);
	}
	return response.json();
}

// Post data to API
export async function postData(url, token, data) {
	let response = await fetch(`/${import.meta.env.VITE_API_BASE_URL}/${url}`, {
		method: "POST",
		headers: {
			Authorization: "Bearer " + String(token),
			"Content-Type": "application/json",
		},
		body: JSON.stringify(data),
	});
	let response_json = await response.json();
	response_json["ok"] = response.ok;
	response_json["statusText"] = response.statusText;
	// if (!response.ok) {
	// 	throw new Error(response.statusText);
	// }
	return response_json;
}

// Patch data to API
export async function patchData(url, token, data) {
	let response = await fetch(`/${import.meta.env.VITE_API_BASE_URL}/${url}`, {
		method: "PATCH",
		headers: {
			Authorization: "Bearer " + String(token),
			"Content-Type": "application/json",
		},
		body: JSON.stringify(data),
	});

	let response_json = await response.json();
	response_json["ok"] = response.ok;
	response_json["statusText"] = response.statusText;

	console.log(response_json);

	//if (!response.ok) {
	//throw new Error(response.statusText);
	//}
	return response_json;
}

// Delete data from API
export async function deleteData(url, token) {
	let response = await fetch(`/${import.meta.env.VITE_API_BASE_URL}/${url}`, {
		method: "DELETE",
		headers: {
			Authorization: "Bearer " + String(token),
			"Content-Type": "application/json",
		},
	});
	console.log(response);
	let response_json = {};
	response_json["ok"] = response.ok;
	response_json["statusText"] = response.statusText;

	console.log(response_json);
	return response_json;
}
