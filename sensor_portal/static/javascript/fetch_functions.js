// Submit data to API
async function SubmitData(url, data, method = "POST") {
  let response = await fetch(url, {
    method: method,
    headers: {
      "X-CSRFToken": document.head.querySelector("meta[name=csrf-token]")
        .content,
    },
    mode: "same-origin",
    body: data,
  });

  let response_json = await response.json();
  response_json["ok"] = response.ok;
  return response_json;
}

// Get data from API
async function getData(url) {
  let response = await fetch(url, {
    headers: {
      "X-CSRFToken": document.head.querySelector("meta[name=csrf-token]")
        .content,
    },
  });

  let response_json = await response.json();
  response_json["ok"] = response.ok;
  return response_json;
}
