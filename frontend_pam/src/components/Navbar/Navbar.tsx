import AuthContext from '@/auth/AuthContext';
import { Link } from '@tanstack/react-router';
import { useContext } from 'react';
import { FaUser } from "react-icons/fa";
import { Menu } from 'lucide-react';

type AuthContextType = {
  user: any;
};

function Navbar() {

  const { user } = useContext(AuthContext) as AuthContextType;
  
  return (
    <nav className="bg-green-900 p-3">
      <div className="flex flex-wrap items-center justify-between w-full">
        <div className="flex items-center space-x-6 ">
          <Link to="/" className="text-white text-3xl sm:text-4xl">PAM</Link>
          <Menu className="text-white text-3xl sm:text-4xl translate-y-0.5" />
        </div>
        <div className="flex items-center space-x-4 mt-2 sm:mt-0">
          <Link to="/" className="hidden sm:block text-white text-lg sm:text-2xl">{user.username}</Link>
          <Link to="/">
            <FaUser className="text-white text-2xl sm:text-3xl" />
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

