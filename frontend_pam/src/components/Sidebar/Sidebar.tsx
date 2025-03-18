import { Link, useLocation } from '@tanstack/react-router'

function Sidebar() {
  const location = useLocation()

  // Sjekker om vi er på en "/devices" side (inkluderer f.eks. "/devices/deviceDashboard")
  const isDevicesActive = location.pathname.startsWith('/device')

  return (
    <div className="h-screen min-w-10 border-r bg-gray-50">
      <nav className="h-full w-64 bg-white">
        <div className="flex flex-col space-y-1 p-3">
          <Link to="/" className="[&.active]:font-bold">Overview</Link>
          
          <Link to="/devices" className={isDevicesActive ? 'font-bold' : ''}>
            Devices
          </Link>

          <Link to="/map" className="[&.active]:font-bold">Map</Link>
        </div>
      </nav>
    </div>
  )
}

export default Sidebar
