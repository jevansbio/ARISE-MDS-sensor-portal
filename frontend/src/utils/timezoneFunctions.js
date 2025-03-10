export const itemFromTimeZone = function (timeZone) {
	return {
		label: timeZone,
		value: timeZone,
	};
};

export const fullDateTimeString = function (
	date,
	timeZone,
	returnFull = false
) {
	let dateParts = new Intl.DateTimeFormat("nu", {
		timeZone: timeZone,
		timeZoneName: "longOffset",
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
		fractionalSecondDigits: 3,
		hour12: false,
	}).formatToParts(date);
	let offset = dateParts
		.find((part) => part.type === "timeZoneName")
		.value.replace("GMT", "");
	if (offset === "") {
		offset = "Z";
	}

	if (!returnFull) {
		return offset;
	}

	let year = dateParts.find((part) => part.type === "year").value;
	let month = dateParts.find((part) => part.type === "month").value;
	let day = dateParts.find((part) => part.type === "day").value;

	let hour = dateParts.find((part) => part.type === "hour").value;
	let minute = dateParts.find((part) => part.type === "minute").value;
	let second = dateParts.find((part) => part.type === "second").value;
	let fractionalSecond = dateParts.find(
		(part) => part.type === "fractionalSecond"
	).value;

	return `${year}-${month}-${day}T${hour}:${minute}:${second}.${fractionalSecond}${offset}`;
};

export const timezonesWithoffsets = Intl.supportedValuesOf("timeZone").map(
	(timeZone) => itemFromTimeZone(timeZone)
);

export const browserTimezone = new Intl.DateTimeFormat("en-GB", {
	timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
	timeZoneName: "short",
})
	.formatToParts()
	.find((part) => part.type === "timeZoneName")
	.value.replace("GMT", "UTC");

// const browserTimezoneOffset = new Intl.DateTimeFormat("en-GB", {
// 	timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
// 	timeZoneName: "longOffset",
// })
// 	.formatToParts()
// 	.find((part) => part.type === "timeZoneName")
// 	.value.replace("GMT", "UTC");
// if (browserTimezoneOffset === "UTC") {
// 	browserTimezoneOffset = "UTC+00:00";
// }

export const getTimeZoneCode = function (datetime) {
	return datetime
		.toLocaleDateString("en-GB", { day: "2-digit", timeZoneName: "short" })
		.substring(4);
};

export const getOffset = function (timeZoneCode, removeUTC = false) {
	//console.log(timeZoneCode);
	let timeZone = timezonesWithoffsets.find(
		(element) => element["abbreviation"] === timeZoneCode
	);
	let offset = timeZone["offset"];
	if (removeUTC) {
		offset = offset.replace("UTC", "");
	}
	return offset;
};

export const dtFormat = new Intl.DateTimeFormat("en-GB", {
	year: "numeric",
	month: "numeric",
	day: "numeric",
	hour: "numeric",
	minute: "numeric",
	second: "numeric",
	timeZoneName: "short",
});

export function convertDateToUTC(date) {
	return new Date(
		date.getUTCFullYear(),
		date.getUTCMonth(),
		date.getUTCDate(),
		date.getUTCHours(),
		date.getUTCMinutes(),
		date.getUTCSeconds()
	);
}

export const nativeTZ = function (date) {
	let newdate = `${date.getFullYear()}-${padInt(date.getMonth() + 1)}-${padInt(
		date.getDate()
	)}T${padInt(date.getHours())}:${padInt(date.getMinutes())}:${padInt(
		date.getSeconds()
	)}.${date.getMilliseconds()}`;
	return newdate;
};

const padInt = function (n) {
	return String(n).padStart(2, "0");
};
