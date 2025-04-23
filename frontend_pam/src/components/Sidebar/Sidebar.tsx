import { Link, useLocation } from '@tanstack/react-router'
import { FaHome, FaMicrochip, FaMap, FaListAlt } from 'react-icons/fa'
import { useState } from 'react';
import { HiMenu, HiX } from 'react-icons/hi';

function Sidebar() {
  const location = useLocation()
  const [isCollapsed, setIsCollapsed] = useState(false);

  const isDevicesActive = location.pathname.startsWith('/device')
  const isObservationsActive = location.pathname.startsWith('/observations')

  return (
<div className={`h-screen border-r bg-gray-50 transition-all duration-300 ${isCollapsed ? 'sm:w-16' : 'w-16 sm:w-64'}`}>


    <nav className="h-full bg-white">
      {/* hide menu button on small screen */}
      <div className="hidden md:flex items-center justify-end p-3">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="rounded-lg p-2 hover:bg-gray-100"
        >
          {isCollapsed ? <HiMenu className="h-6 w-6" /> : <HiX className="h-6 w-6" />}
        </button>
      </div>
        <div className="flex flex-col space-y-1 p-3">
          <Link 
            to="/" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-gray-700 hover:bg-gray-100 [&.active]:font-bold [&.active]:bg-gray-100 ${isCollapsed ? 'justify-center' : ''}`}
          >
            <FaHome className="h-5 w-5" />
            {!isCollapsed && <span className="hidden md:inline">Overview</span>}
          </Link>
          
          <Link 
            to="/deployments" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-gray-700 hover:bg-gray-100 ${isDevicesActive ? 'font-bold bg-gray-100' : ''} ${isCollapsed ? 'justify-center' : ''}`}
          >
            <FaMicrochip className="h-5 w-5" />
            {!isCollapsed && <span className="hidden md:inline">Deployments</span>}
          </Link>

          <Link 
            to="/map" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-gray-700 hover:bg-gray-100 [&.active]:font-bold [&.active]:bg-gray-100 ${isCollapsed ? 'justify-center' : ''}`}
          >
            <FaMap className="h-5 w-5" />
            {!isCollapsed && <span className="hidden md:inline">Map</span>}
          </Link>

          <Link 
            to="/observations" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-gray-700 hover:bg-gray-100 ${isObservationsActive ? 'font-bold bg-gray-100' : ''} ${isCollapsed ? 'justify-center' : ''}`}
          >
            <FaListAlt className="h-5 w-5" />
            {!isCollapsed && <span className="hidden md:inline">Observations</span>}
          </Link>
        </div>
      </nav>
    </div>
  )
}

export default Sidebar
