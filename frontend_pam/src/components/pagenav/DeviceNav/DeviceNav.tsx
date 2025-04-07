interface DeviceNavProps {
  activeTab: 'details' | 'datafiles'| 'siteDetails' | 'map';
  setActiveTab: (tab: 'details' | 'datafiles' | 'siteDetails' | 'map') => void;
}

function DeviceNav({ activeTab, setActiveTab }: DeviceNavProps) {
  return (
    <nav className="border-b border-gray-200">
      <ul className="flex flex-row gap-8 px-6">
      <li>
          <button
            onClick={() => setActiveTab('siteDetails')}
            className={`inline-block py-4 text-lg hover:text-gray-600 ${
              activeTab === 'siteDetails' ? 'border-b-2 border-black' : ''
            }`}
          >
            Site Details
          </button>
        </li>
        <li>
          <button
            onClick={() => setActiveTab('details')}
            className={`inline-block py-4 text-lg hover:text-gray-600 ${
              activeTab === 'details' ? 'border-b-2 border-black' : ''
            }`}
          >
            Device Details
          </button>
        </li>
        <li>
          <button
            onClick={() => setActiveTab('datafiles')}
            className={`inline-block py-4 text-lg hover:text-gray-600 ${
              activeTab === 'datafiles' ? 'border-b-2 border-black' : ''
            }`}
          >
            Data Files
          </button>
        </li>
        <li>
          <button
            onClick={() => setActiveTab('map')}
            className={`inline-block py-4 text-lg hover:text-gray-600 ${
              activeTab === 'map' ? 'border-b-2 border-black' : ''
            }`}
          >
            Map
          </button>
        </li>
      </ul>
    </nav>
  );
}

export default DeviceNav;
