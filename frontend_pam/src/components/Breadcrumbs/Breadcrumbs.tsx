import { Link, useLocation } from '@tanstack/react-router';

const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1);

function Breadcrumbs() {
  const location = useLocation();
  const paths = location.pathname.split('/').filter((segment) => segment);

  const breadcrumbs = paths.map((segment, index) => {
    const path = '/' + paths.slice(0, index + 1).join('/');
    return { label: capitalize(segment), path };
  });

  const currentPage = breadcrumbs.length > 0 ? breadcrumbs[breadcrumbs.length - 1].label : 'Overview';

  return (
    <>
      <h1 className="text-lg lg:text-2xl font-bold px-3 py-2 ">{currentPage}</h1>
      <nav className="p-3 w-full border-b border-gray-300 hidden sm:block">
        <ol className="list-reset flex text-black">
          <li>
            <Link to="/" className="hover:underline text-black">Overview</Link>
            {paths.length > 0 && <span className="mx-2">&gt;</span>}
          </li>
          {breadcrumbs.map((breadcrumb, index) => (
            <li key={breadcrumb.path} className="flex items-center">
              <Link to={breadcrumb.path} className="hover:underline text-black">
                {breadcrumb.label}
              </Link>
              {index < breadcrumbs.length - 1 && <span className="mx-2">&gt;</span>}
            </li>
          ))}
        </ol>
      </nav>
    </>
  );
}


export default Breadcrumbs;

