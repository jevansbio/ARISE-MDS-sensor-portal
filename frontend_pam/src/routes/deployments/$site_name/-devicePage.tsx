import { useState } from 'react';
import DeviceNav from '@/components/pagenav/DeviceNav';
import DeviceDataFilesPage from './-deviceDataFilesPage';
import DeviceDetailPage from './-deviceDetailPage';
import SiteDetailPage from './-SiteDetailPage';
import DeploymentMapPage from './-deploymentMapPage';

export default function DevicePage() {
  const [activeTab, setActiveTab] = useState<'details' | 'datafiles' | 'siteDetails' | 'map'>('siteDetails'); 

  return (
    <div>
      {/* Render the device navigation component */}
      <DeviceNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />
      {activeTab === 'siteDetails' && (
        <SiteDetailPage />
      )}
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
