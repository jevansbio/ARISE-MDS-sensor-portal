// Get data from API
export async function getData(url, token) {
	let response = await fetch(`/${import.meta.env.VITE_API_BASE_URL}/${url}`, {
		headers: {
			Authorization: "Bearer " + String(token),
			"Content-Type": "application/json",
		},
	});
	if (!response.ok) {
		// Try to get error details from response
		try {
			const errorData = await response.json();
			throw new Error(
				errorData.detail || 
				errorData.message || 
				`${response.status} ${response.statusText}`
			);
		} catch (e) {
			// If we can't parse the error JSON, throw the status
			throw new Error(`${response.status} ${response.statusText}`);
		}
	}
	return response.json();
}

// Post data to API
export async function postData(url, token, data, method = 'POST') {
	let response = await fetch(`/${import.meta.env.VITE_API_BASE_URL}/${url}`, {
		method: method,
		headers: {
			Authorization: "Bearer " + String(token),
			"Content-Type": "application/json",
		},
		body: JSON.stringify(data),
	});

	if (!response.ok) {
		// Try to get error details from response
		try {
			const errorData = await response.json();
			throw new Error(
				errorData.detail || 
				errorData.message || 
				`${response.status} ${response.statusText}`
			);
		} catch (e) {
			// If we can't parse the error JSON, throw the status
			throw new Error(`${response.status} ${response.statusText}`);
		}
	}

	return response.json();
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
