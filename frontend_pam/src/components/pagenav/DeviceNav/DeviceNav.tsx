interface DeviceNavProps {
  activeTab: 'details' | 'datafiles';
  setActiveTab: (tab: 'details' | 'datafiles') => void;
}

function DeviceNav({ activeTab, setActiveTab }: DeviceNavProps) {
  return (
    <nav className="border-b border-gray-200">
      <ul className="flex flex-row gap-8 px-6">
        <li>
          <button
            onClick={() => setActiveTab('details')}
            className={`inline-block py-4 text-lg hover:text-gray-600 ${
              activeTab === 'details' ? 'border-b-2 border-black' : ''
            }`}
          >
            Details
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
      </ul>
    </nav>
  );
}

export default DeviceNav;
