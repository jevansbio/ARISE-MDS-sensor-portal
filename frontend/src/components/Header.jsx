import { NavLink, Link } from "react-router-dom";
import AuthContext from "../context/AuthContext";
import { useContext } from "react";
import "../styles/header.css";

// eslint-disable-next-line no-unused-vars
import { Offcanvas } from "bootstrap";

const Header = () => {
	let { user, logoutUser } = useContext(AuthContext);

	return (
		<nav
			className="navbar bg-dark navbar-expand-lg fixed-top"
			data-bs-theme="dark"
		>
			<div className="container-fluid">
				<NavLink
					className="navbar-brand"
					to="/"
				>
					Sensor portal
				</NavLink>
				<button
					className="navbar-toggler"
					type="button"
					data-bs-toggle="offcanvas"
					data-bs-target="#offcanvasNavbar"
					aria-controls="offcanvasNavbar"
					aria-label="Toggle navigation"
				>
					<span className="navbar-toggler-icon"></span>
				</button>
				<div
					className="offcanvas offcanvas-top text-bg-dark"
					tabIndex="-1"
					id="offcanvasNavbar"
					aria-labelledby="offcanvasNavbarLabel"
				>
					<div className="offcanvas-header">
						<h5
							className="offcanvas-title"
							id="offcanvasDarkNavbarLabel"
						>
							Menu
						</h5>
						<button
							type="button"
							className="btn-close btn-close-white"
							data-bs-dismiss="offcanvas"
							aria-label="Close"
						></button>
					</div>
					<div className="offcanvas-body">
						<ul className="navbar-nav justify-content-end">
							<li className="nav-item">
								<NavLink
									className="nav-link"
									to="/"
								>
									Home
								</NavLink>
							</li>
							{user && (
								<>
									<li className="nav-item">
										<NavLink
											className="nav-link"
											to="/projects"
										>
											Projects
										</NavLink>
									</li>
									<li className="nav-item">
										<NavLink
											className="nav-link"
											to="/devices"
										>
											Devices
										</NavLink>
									</li>
									<li className="nav-item">
										<NavLink
											className="nav-link"
											to="/deployments"
										>
											Deployments
										</NavLink>
									</li>
									<li className="nav-item">
										<NavLink
											className="nav-link"
											to="/datafiles"
										>
											Datafiles
										</NavLink>
									</li>
								</>
							)}
						</ul>
						<ul className="navbar-nav ms-lg-auto">
							{user && (
								<li className="nav-item dropdown">
									<Link
										className="nav-link dropdown-toggle"
										role="button"
										data-bs-toggle="dropdown"
										aria-expanded="false"
									>
										{user.username}
									</Link>
									<ul className="dropdown-menu dropdown-menu-end">
										<li className="dropdown-item">
											<Link
												onClick={logoutUser}
												className="nav-link"
												to="#"
											>
												Logout
											</Link>
										</li>
									</ul>
								</li>
							)}
						</ul>
					</div>
				</div>
			</div>
		</nav>
	);
};

export default Header;
