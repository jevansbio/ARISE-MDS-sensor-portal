import { useState } from 'react';
import DeviceNav from '@/components/pagenav/DeviceNav';
import DeviceAudioFilesPage from './-deviceDataFilesPage';
import DeviceDetailPage from './-deviceDetailPage';

export default function DevicePage() {
  const [activeTab, setActiveTab] = useState<'details' | 'audioFiles'>('details'); 

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
    </div>
  );
}
