interface DeploymentNavProps {
  activeTab: 'deviceDetails' | 'datafiles'| 'siteDetails' | 'map';
  setActiveTab: (tab: 'deviceDetails' | 'datafiles' | 'siteDetails' | 'map') => void;
}

function DeploymentNav({ activeTab, setActiveTab }: DeploymentNavProps) {
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
            onClick={() => setActiveTab('deviceDetails')}
            className={`inline-block py-4 text-lg hover:text-gray-600 ${
              activeTab === 'deviceDetails' ? 'border-b-2 border-black' : ''
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

export default DeploymentNav;
