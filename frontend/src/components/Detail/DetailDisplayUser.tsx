import React from "react";
import { Link } from "react-router-dom";
import { getData } from "../../utils/FetchFunctions";
import { useQuery } from "@tanstack/react-query";
import Loading from "../General/Loading.tsx";

interface DataListProps {
	title: string;
	data: string[];
	ids: string[];
	basePath: string;
	className?: string;
}

const DataList = ({
	title,
	data,
	ids,
	basePath,
	className = "col m-2 small overflow-y-auto w-lg-25",
}: DataListProps) => {
	console.log(title);
	return (
		<div
			className={className}
			style={{ maxHeight: "15rem" }}
		>
			<strong>{title}:</strong>
			<ul className="list-group">
				{data.map((item, index) => (
					<li
						className="list-group-item list-group-item-action overflow-hidden "
						key={index}
					>
						<Link
							to={`${basePath}/${ids[index]}`}
							style={{ color: "inherit", textDecoration: "inherit" }}
						>
							{item}
						</Link>
					</li>
				))}
			</ul>
		</div>
	);
};

interface UserProfileProps {
	id: string | undefined;
	authTokens: any;
	user: any;
}

const DetailDisplayUser = ({ id, authTokens, user }: UserProfileProps) => {
	const getDataFunc = async () => {
		let apiURL = `userprofile/${id}`;
		let response_json = await getData(apiURL, authTokens.access);
		return response_json;
	};

	const {
		isLoading,
		isError,
		//isPending,
		data,
		error,
		//isPlaceholderData,
		//refetch,
	} = useQuery({
		queryKey: ["profile", user],
		queryFn: () => getDataFunc(),
		refetchOnWindowFocus: false,
	});

	return (
		<div>
			<title>User profile</title>
			<h3>Profile</h3>
			{isLoading && <Loading />}
			{isError && <p>Error: {error.message}</p>}
			{data && (
				<>
					<dl className="row mb-3">
						<dt className="col-sm-3">Username:</dt>
						<dd className="col-sm-9">{data.username}</dd>

						<dt className="col-sm-3">User ID:</dt>
						<dd className="col-sm-9">{data.id}</dd>

						<dt className="col-sm-3">First Name:</dt>
						<dd className="col-sm-9">{data.first_name}</dd>

						<dt className="col-sm-3">Last Name:</dt>
						<dd className="col-sm-9">{data.last_name}</dd>

						<dt className="col-sm-3">Email:</dt>
						<dd className="col-sm-9">{data.email}</dd>

						<dt className="col-sm-3">Organisation:</dt>
						<dd className="col-sm-9">{data.organisation}</dd>

						<dt className="col-sm-3">Bio:</dt>
						<dd className="col-sm-9">{data.bio}</dd>
					</dl>
					<div className="mb-3 mt-3">
						<Link
							to={`/users/favourites`}
							className="p-2 flex-fill"
						>
							<button className="btn btn-primary w-100">Show favourites</button>
						</Link>
					</div>

					<div className="mb-3">
						<h4>Projects</h4>
						<div className="row">
							<DataList
								title="Owned Projects"
								data={data.owned_projects}
								ids={data.owned_projects_ID}
								basePath="/projects"
							/>
							<DataList
								title="Managed Projects"
								data={data.managed_projects}
								ids={data.managed_projects_ID}
								basePath="/projects"
							/>
							<DataList
								title="Annotatable Projects"
								data={data.annotatable_projects}
								ids={data.annotatable_projects_ID}
								basePath="/projects"
							/>
							<DataList
								title="Viewable Projects"
								data={data.viewable_projects}
								ids={data.viewable_projects_ID}
								basePath="/projects"
							/>
						</div>
					</div>
					<div className="mb-3">
						<h4>Devices</h4>
						<div className="row">
							<DataList
								title="Owned Devices"
								data={data.owned_devices}
								ids={data.owned_devices_ID}
								basePath="/devices"
							/>
							<DataList
								title="Managed Devices"
								data={data.managed_devices}
								ids={data.managed_devices_ID}
								basePath="/devices"
							/>
							<DataList
								title="Annotatable Devices"
								data={data.annotatable_devices}
								ids={data.annotatable_devices_ID}
								basePath="/devices"
							/>
							<DataList
								title="Viewable Devices"
								data={data.viewable_devices}
								ids={data.viewable_devices_ID}
								basePath="/devices"
							/>
						</div>
					</div>
					<div className="mb-3">
						<h4>Deployments</h4>
						<div className="row">
							<DataList
								title="Owned Deployments"
								data={data.owned_deployments}
								ids={data.owned_deployments_ID}
								basePath="/deployments"
							/>
							<DataList
								title="Managable Deployments"
								data={data.managed_deployments}
								ids={data.managed_deployments_ID}
								basePath="/deployments"
							/>
							<DataList
								title="Annotatable Deployments"
								data={data.annotatable_deployments}
								ids={data.annotatable_deployments_ID}
								basePath="/deployments"
							/>
							<DataList
								title="Viewable Deployments"
								data={data.viewable_deployments}
								ids={data.viewable_deployments_ID}
								basePath="/deployments"
							/>
						</div>
					</div>
				</>
			)}
		</div>
	);
};

export default DetailDisplayUser;
