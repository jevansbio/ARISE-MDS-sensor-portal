import { useState } from 'react';
import DeviceNav from '@/components/pagenav/DeploymentNav';
import DeviceDataFilesPage from './-deviceDataFilesPage';
import DeviceDetailPage from './-deviceDetailPage';
import DeploymentMapPage from './-deploymentMapPage';
import SiteDetailPage from './-siteDetailPage';

export default function DeploymentPage() {
  const [activeTab, setActiveTab] = useState<'deviceDetails' | 'datafiles' | 'siteDetails' | 'map'>('siteDetails'); 

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
      {activeTab === 'deviceDetails' && (
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
