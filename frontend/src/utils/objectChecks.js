const validObjects = ["deployment", "device", "project", "datafile"];

const nameKeys = {
	deployment: "deployment_device_ID",
	device: "device_ID",
	project: "project_ID",
	datafile: "file_name",
};

const validGalleries = {
	deployment: ["datafile"],
	device: ["deployment", "datafile"],
	project: ["deployment", "datafile"],
	datafile: [],
};

const validParents = {
	deployment: ["device", "project"],
	device: [],
	project: [],
	datafile: ["deployment"],
};

export const getNameKey = function (objectType) {
	return nameKeys[objectType];
};

export const getValidGalleries = function (fromObject) {
	return validGalleries[fromObject];
};

export const getValidParents = function (fromObject) {
	return validParents[fromObject];
};

export const getValidObject = function (objectType) {
	return validObjects.includes(objectType);
};
