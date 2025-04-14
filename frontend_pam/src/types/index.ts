// Device and Deployment Types
export type Device = {
    id: string;
    startDate: string;
    endDate: string;
    lastUpload: string;
    batteryLevel: number;
    folder_size: number;
    action: string;
    site: string;
    dataFile: DataFile[];
};

export type Deployment = {
    deploymentId: string;
    startDate: string;
    endDate: string;
    lastUpload: string;
    batteryLevel: number;
    siteName: string;
    folderSize: number;
    coordinateUncertainty: string;
    gpsDevice: string;
    micHeight: number;
    micDirection: string;
    latitude: number;
    longitude: number;
    habitat: string;
    protocolChecklist: string;
    score: number;
    comment: string;
    action: string;
    userEmail: string;
    country: string;
};

// Data File Types
export interface ExtraData {
    quality_metrics?: Record<string, any>;
    temporal_evolution?: Record<string, any>;
    observations?: string[];
    auto_detected_observations: number[];
}

export type DataFile = {
    id: string;
    deployment: string;
    fileName: string;
    fileFormat: string;
    fileSize: number;
    fileType: string;
    path: string;
    localPath: string;
    uploadDt: string;
    recordingDt: string;
    // Audio file specific fields
    config: string | null;
    sampleRate: number | null;
    fileLength: string | null;
    // Quality check fields
    qualityScore: number | null;
    qualityIssues: string[];
    qualityCheckDt: string | null;
    qualityCheckStatus: 'pending' | 'in_progress' | 'completed' | 'failed';
    // Additional fields
    extraData: ExtraData | null;
    thumbUrl: string | null;
    localStorage: boolean;
    archived: boolean;
    favourite: boolean;
};

// Observation Types
export interface Observation {
    id: number;
    obs_dt: string;
    source: string;
    needs_review: boolean;
    extra_data: {
        start_time: number;
        end_time: number;
        duration: number;
        avg_amplitude: number;
        auto_detected: boolean;
        needs_review?: boolean;
    };
    taxon: {
        species_name: string;
        species_common_name: string;
        id: number;
    };
    data_files: Array<{
        id: number;
        file_name: string;
        deployment?: {
            name: string;
            device: {
                name: string;
                id: string;
            };
        };
    }>;
}

// UI Component Types
export type ModalProps = {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
}; 