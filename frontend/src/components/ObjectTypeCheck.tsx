import React, { createContext } from "react";
import { Outlet, useParams } from "react-router-dom";
import {
	getNameKey,
	getValidGalleries,
	getValidParents,
	getValidObject,
} from "../utils/objectChecks";
import Error404page from "../pages/Error404page";

export const ObjectTypeCheck = () => {
	let { fromObject, fromID, objectType } = useParams();

	if (objectType === undefined) {
		objectType = fromObject;
		fromObject = undefined;
	} else if (fromObject !== undefined) {
		fromObject = fromObject.substring(0, fromObject.length - 1);
	}
	if (objectType !== undefined) {
		objectType = objectType.substring(0, objectType.length - 1);
	}

	let error = false;

	const isValidObject = getValidObject(objectType);
	if (!isValidObject) {
		error = true;
	}

	const nameKey = getNameKey(objectType);
	if (fromID !== undefined && fromObject !== undefined) {
		const validFromGalleries = getValidGalleries(fromObject);
		if (
			validFromGalleries === undefined ||
			!validFromGalleries.includes(objectType)
		) {
			error = true;
		}
	}

	const validGalleries = getValidGalleries(objectType);
	const validParents = getValidParents(objectType);

	const contextData = {
		fromObject: fromObject,
		fromID: fromID,
		objectType: objectType,
		nameKey: nameKey,
		validGalleries: validGalleries,
		validParents: validParents,
	};

	console.log(contextData);

	if (error) {
		return <Error404page />;
	}

	return <Outlet context={contextData} />;
};

export default ObjectTypeCheck;
