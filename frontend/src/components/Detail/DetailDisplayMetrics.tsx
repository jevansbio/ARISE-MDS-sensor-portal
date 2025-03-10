import React, { useContext, useEffect, useState } from "react";

import { getData } from "../../utils/FetchFunctions.js";
import Loading from "../Loading.tsx";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import AuthContext from "../../context/AuthContext.jsx";
import { capitalizeFirstLetter } from "../../utils/generalFunctions.js";
import MetricPlot from "./MetricPlot.tsx";
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "react-tabs/style/react-tabs.css";

interface Props {
	id: number;
	objectType: string;
}

const DetailDisplayMetrics = ({ id, objectType }: Props) => {
	const { authTokens, user } = useContext(AuthContext);
	const [currentMetric, setCurrentMetric] = useState<string>();

	const getDataFunc = async () => {
		let apiURL = `${objectType}/${id}/metrics`;
		console.log(apiURL);
		let response_json = await getData(apiURL, authTokens.access);
		return response_json;
	};

	const {
		isLoading,
		isError,
		isPending,
		data,
		error,
		isRefetching,
		isPlaceholderData,
		refetch,
	} = useQuery({
		queryKey: ["metrics", user, id, objectType],
		queryFn: () => getDataFunc(),
		placeholderData: keepPreviousData,
	});

	const getTabs = function () {
		const tabs = Object.keys(data).map((key) => {
			console.log(key);
			return <Tab>{capitalizeFirstLetter(key.replace(/_/g, " "))}</Tab>;
		});
		return tabs;
	};

	const getTabContent = function () {
		const tabContent = Object.keys(data).map((key) => {
			console.log(key);
			return (
				<TabPanel>
					<div
						style={{
							display: "flex",
							justifyContent: "center",
						}}
					>
						<MetricPlot data={data[key]} />
					</div>
				</TabPanel>
			);
		});
		return tabContent;
	};

	useEffect(() => {
		if (
			data &&
			(!currentMetric || !Object.keys(data).includes(currentMetric))
		) {
			setCurrentMetric(Object.keys(data)[0]);
		}
	}, [currentMetric, data]);

	if (isLoading || isPending || isRefetching) {
		return <Loading />;
	}

	if (!data || !currentMetric) {
		return null;
	} else {
		return (
			<Tabs>
				<TabList>{getTabs()}</TabList>
				{getTabContent()}
			</Tabs>
		);
	}
};

export default DetailDisplayMetrics;
