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
    config: string;
    samplerate: number;
    fileLength: string;
    fileSize: number;
    fileFormat: string;
};

export type ModalProps = {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
};