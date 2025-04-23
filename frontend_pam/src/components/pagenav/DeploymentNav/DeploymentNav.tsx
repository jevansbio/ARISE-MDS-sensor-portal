import {
  FaMapMarkerAlt,
  FaMicrochip,
  FaDatabase,
  FaMap,
} from 'react-icons/fa';

interface DeploymentNavProps {
  activeTab: 'deviceDetails' | 'datafiles' | 'siteDetails' | 'map';
  setActiveTab: (tab: 'deviceDetails' | 'datafiles' | 'siteDetails' | 'map') => void;
}

function DeploymentNav({ activeTab, setActiveTab }: DeploymentNavProps) {
  const tabs = [
    { key: 'siteDetails', label: 'Site', labelFull: 'Site Details', icon: FaMapMarkerAlt },
    { key: 'deviceDetails', label: 'Device', labelFull: 'Device Details', icon: FaMicrochip },
    { key: 'datafiles', label: 'Data', labelFull: 'Data Files', icon: FaDatabase },
    { key: 'map', label: 'Map', labelFull: 'Map', icon: FaMap },
  ] as const;

  return (
    <nav className="border-b border-gray-200">
      <ul className="flex justify-between sm:justify-start sm:gap-8 px-4 sm:px-6">
        {tabs.map(({ key, label, labelFull, icon: Icon }) => (
          <li key={key}>
            <button
              onClick={() => setActiveTab(key)}
              className={`flex flex-col items-center sm:inline-block py-4 text-sm sm:text-lg hover:text-gray-600 transition-all ${
                activeTab === key ? 'border-b-2 border-black text-black' : ''
              }`}
            >
              <Icon className="sm:hidden" size={18} />
              <span className="hidden sm:inline">{labelFull}</span>
              <span className="sm:hidden text-xs mt-1">{label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default DeploymentNav;
