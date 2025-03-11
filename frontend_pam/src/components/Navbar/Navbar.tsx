import { Link } from '@tanstack/react-router';
import { FaUser } from "react-icons/fa6";
import { LuMenu } from "react-icons/lu";

function Navbar() {
  return (
    <nav className="bg-green-900 p-3">
      <div className="flex flex-wrap items-center justify-between w-full">
        <div className="flex items-center space-x-6 ">
          <Link to="/" className="text-white text-3xl sm:text-4xl">PAM</Link>
          <LuMenu className="text-white text-3xl sm:text-4xl translate-y-0.5" />
        </div>
        <div className="flex items-center space-x-4 mt-2 sm:mt-0">
          <Link to="/" className="hidden sm:block text-white text-lg sm:text-2xl">Username</Link>
          <Link to="/">
            <FaUser className="text-white text-2xl sm:text-3xl" />
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

