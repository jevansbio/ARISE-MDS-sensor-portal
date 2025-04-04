import { useState } from 'react';
import DeviceNav from '@/components/pagenav/DeviceNav';
import DeviceAudioFilesPage from './-deviceDataFilesPage';
import DeviceDetailPage from './-deviceDetailPage';
import SiteDetailPage from './-SiteDetailPage';

export default function DevicePage() {
  const [activeTab, setActiveTab] = useState<'details' | 'audioFiles' | 'siteDetails'>('details'); 

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

      {activeTab === 'audioFiles' && (
        <DeviceAudioFilesPage />
      )}
      {activeTab === 'siteDetails' && (
        <SiteDetailPage />
      )}
    </div>
  );
}
