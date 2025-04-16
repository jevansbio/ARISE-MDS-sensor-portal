import { useContext } from 'react';
import AuthContext from '@/auth/AuthContext';
import { Link } from '@tanstack/react-router';
import { FaUser, FaDoorClosed } from "react-icons/fa";

type UserType = {
  username: string;
  // Add other user properties as needed
};

type AuthContextType = {
  user: UserType | null;
  logoutUser: () => void;
};

function Navbar() {
  const { user, logoutUser } = useContext(AuthContext) as AuthContextType;

  const handleLogout = () => {
    if (window.confirm("Are you sure you want to log out?")) {
      logoutUser();
    }
  };

  return (
    <nav className="bg-green-900 p-3">
      <div className="flex flex-wrap items-center justify-between w-full">
        <div className="flex items-center space-x-6 ">
          <Link to="/" className="text-white text-3xl sm:text-4xl">PAM</Link>
        </div>
        <div className="flex items-center space-x-4 mt-2 sm:mt-0">
          
          <Link to="/" className="sm:block text-white text-lg sm:text-2xl">
            {user?.username}
          </Link>
          <Link to="/">
            <FaUser className="text-white text-2xl sm:text-3xl" />
          </Link>
          <button 
            onClick={handleLogout} 
            className="border border-white rounded px-3 py-1 flex items-center space-x-2 text-white text-lg sm:text-2xl"
          >
            <FaDoorClosed className="text-white" />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

