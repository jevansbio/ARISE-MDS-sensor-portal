import { useState } from 'react';
import DeviceNav from '@/components/pagenav/DeviceNav';
import DeviceDataFilesPage from './-deviceDataFilesPage';
import DeviceDetailPage from './-deviceDetailPage';
import DeploymentMapPage from './-deploymentMapPage';

export default function DevicePage() {
  const [activeTab, setActiveTab] = useState<'details' | 'datafiles' | 'map'>('details'); 

  return (
    <div>
      {/* Render the device navigation component */}
      <DeviceNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {activeTab === 'details' && (
        <DeviceDetailPage />
      )}

      {activeTab === 'datafiles' && (
        <DeviceDataFilesPage />
      )}

      {activeTab === 'map' && (
        <DeploymentMapPage />
      )}
    </div>
  );
}
