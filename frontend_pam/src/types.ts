export type Device = {
    id: string;
    project: string;
    startDate: string;
    endDate: string;
    lastUpload: string;
    batteryLevel: number;
    folderSize: string;
    action: string;
    dataFile: DataFile[];
};

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
    extraData: Record<string, any> | null;
    thumbUrl: string | null;
    localStorage: boolean;
    archived: boolean;
    favourite: boolean;
};

export type ModalProps = {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
};